"""
davinci.py

Zakładka "DAVINCI RESOLVE": użytkownik dostarcza gotowy plik audio (nie TTS!),
a backend buduje timeline do DaVinci Resolve:
  1. napisy (SRT) z timestampami,
  2. karty postaci (FCPXML z nameplates).

Tryby (hybryda):
  - audio + skrypt (bloki `[{character_id, text}]` z parsera `Postać: [Dialog]`,
    jak w ReZeroMode) -> zdania skryptu dopasowywane do transkrypcji Whispera
    (ground-truth tekst, Whisper tylko dla TIMINGU — jak w process_audiobook_task),
  - samo audio -> napisy z samej transkrypcji Whispera, całość jako narrator.

Powstale pliki: audiobooks/timelines/captions_{task_id}.srt oraz
nameplates_{task_id}.fcpxml (do pobrania przez /timelines/...).
"""

import difflib
import json
import os
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from pydub import AudioSegment

from db import models
from db.database import SessionLocal
from .alignment import (
    _normalize_word,
    get_audio_duration_seconds,
    normalize_audio_format,
    split_into_sentences,
    transcribe_chunk_words,
)
from .timeline_export import export_all
from .tts import (
    NAMEPLATE_CACHE_DIR,
    TEMP_AUDIO_DIR,
    TIMELINE_OUTPUT_DIR,
    unload_tts_worker,
)

router = APIRouter(
    prefix="/davinci",
    tags=["davinci"],
)

CHUNK_MS = 5 * 60 * 1000  # 5-minutowe kawalki -> stabilna transkrypcja + postep
FALLBACK_SENTENCE_SECONDS = 1.0  # czas niezgodnego zdania w trybie fallbacku
SENTENCE_ENDINGS = (".", "!", "?", "…")

tasks_db: Dict[str, Dict] = {}


def _unload_all_tts_workers():
    from .tts import TTS_WORKER_UNLOAD_URLS
    for provider_name in TTS_WORKER_UNLOAD_URLS:
        unload_tts_worker(provider_name)


def _split_audio_into_chunks(audio_path: str, task_id: str) -> List[Dict]:
    """Tnie audio na kawalki ~5 min. Zwraca [{path, offset_seconds}]."""
    audio = AudioSegment.from_file(audio_path)
    chunks = []
    for start_ms in range(0, max(len(audio), 1), CHUNK_MS):
        segment = audio[start_ms:start_ms + CHUNK_MS]
        out_path = os.path.join(TEMP_AUDIO_DIR, f"davinci_{task_id}_{len(chunks)}.wav")
        segment.export(out_path, format="wav")
        normalize_audio_format(out_path)
        chunks.append({"path": out_path, "offset": start_ms / 1000.0})
    return chunks


def _transcribe_all_chunks(chunks: List[Dict], language: str, task_id: str) -> List[Dict]:
    """Transkrybuje kawalki i scala slowa z offsetami do globalnego czasu pliku."""
    all_words: List[Dict] = []
    for idx, chunk in enumerate(chunks):
        tasks_db[task_id] = {
            "status": "processing",
            "message": f"Transkrypcja (Whisper) {idx + 1}/{len(chunks)}...",
        }
        words = transcribe_chunk_words(chunk["path"], language=language)
        for w in words:
            all_words.append({
                "word": w["word"],
                "start": w["start"] + chunk["offset"],
                "end": w["end"] + chunk["offset"],
            })
    return all_words


def _cleanup_chunks(chunks: List[Dict]) -> None:
    for chunk in chunks:
        try:
            if os.path.exists(chunk["path"]):
                os.remove(chunk["path"])
        except OSError:
            pass


def _words_to_sentence_segments(words: List[Dict], total_duration: float) -> List[Dict]:
    """Grupuje slowa Whispera w zdanio-podobne napisy (tryb bez skryptu)."""
    sentences: List[Dict] = []
    current: List[Dict] = []

    def flush():
        if not current:
            return
        sentences.append({
            "text": " ".join(w["word"] for w in current).strip(),
            "start": current[0]["start"],
            "end": current[-1]["end"],
        })
        current.clear()

    for w in words:
        current.append(w)
        if w["word"].rstrip().endswith(SENTENCE_ENDINGS):
            flush()
    flush()

    # scal zbyt krotkie fragmenty z poprzednim (mniej migajacych napisow)
    merged: List[Dict] = []
    for seg in sentences:
        if merged and (seg["end"] - seg["start"]) < 1.0:
            merged[-1]["end"] = seg["end"]
            merged[-1]["text"] += " " + seg["text"]
        else:
            merged.append(seg)

    if merged:
        merged[0]["start"] = 0.0
        merged[-1]["end"] = max(merged[-1]["end"], total_duration)
    return merged


def _align_script_to_words(
    script_sentences: List[Dict],
    whisper_words: List[Dict],
    total_duration: float,
) -> List[Dict]:
    """
    Dopasowuje znane zdania skryptu do globalnego strumienia slow Whispera
    (analogia do align_sentences_to_timestamps, ale na calym pliku — zdania
    moga swobodnie przechodzic przez granice kawalkow).
    """
    ref_words: List[str] = []
    ref_word_to_sentence: List[int] = []
    for s_idx, sentence in enumerate(script_sentences):
        for w in sentence["text"].split():
            ref_words.append(_normalize_word(w))
            ref_word_to_sentence.append(s_idx)

    hyp_words = [_normalize_word(w["word"]) for w in whisper_words]

    matcher = difflib.SequenceMatcher(a=ref_words, b=hyp_words, autojunk=False)
    sentence_times: Dict[int, list] = {}
    for block in matcher.get_matching_blocks():
        for i in range(block.size):
            s_idx = ref_word_to_sentence[block.a + i]
            t = whisper_words[block.b + i]
            if s_idx not in sentence_times:
                sentence_times[s_idx] = [t["start"], t["end"]]
            else:
                sentence_times[s_idx][0] = min(sentence_times[s_idx][0], t["start"])
                sentence_times[s_idx][1] = max(sentence_times[s_idx][1], t["end"])

    results = []
    last_end = 0.0
    for s_idx, sentence in enumerate(script_sentences):
        if s_idx in sentence_times:
            start, end = sentence_times[s_idx]
            start = max(start, last_end)
            end = max(end, start + 0.1)
        else:
            start = last_end
            end = min(last_end + FALLBACK_SENTENCE_SECONDS, total_duration)
        results.append({**sentence, "start": start, "end": end})
        last_end = end

    if results:
        results[0]["start"] = 0.0
        results[-1]["end"] = max(results[-1]["end"], total_duration)
    return results


def process_davinci_task(task_id: str, audio_path: str, script_sentences: List[Dict], language: str):
    chunks: List[Dict] = []
    try:
        normalize_audio_format(audio_path)
        total_duration = get_audio_duration_seconds(audio_path)

        # VRAM na Whispera: zwolnij modele TTS (Whisper załaduje się leniwie)
        _unload_all_tts_workers()

        tasks_db[task_id] = {"status": "processing", "message": "Analiza audio..."}
        chunks = _split_audio_into_chunks(audio_path, task_id)
        whisper_words = _transcribe_all_chunks(chunks, language, task_id)

        if script_sentences:
            if not whisper_words:
                raise RuntimeError(
                    "Whisper nie rozpoznał żadnej mowy w pliku audio — nie da się dopasować skryptu."
                )
            tasks_db[task_id] = {"status": "processing", "message": "Dopasowywanie skryptu do audio..."}
            timed = _align_script_to_words(script_sentences, whisper_words, total_duration)
        else:
            timed = _words_to_sentence_segments(whisper_words, total_duration)
            if not timed:
                raise RuntimeError("Nie rozpoznano żadnej mowy w pliku audio.")

        segments = [{
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
            "character_id": seg.get("character_id"),
            "character_name": seg.get("character_name"),
            "avatar_path": seg.get("avatar_path"),
            "is_narrator": seg.get("is_narrator", seg.get("character_id") is None),
        } for seg in timed]

        tasks_db[task_id] = {"status": "processing", "message": "Eksport timeline'u (SRT + FCPXML)..."}
        timeline_files = export_all(
            segments=segments,
            output_dir=TIMELINE_OUTPUT_DIR,
            task_id=task_id,
            nameplate_cache_dir=NAMEPLATE_CACHE_DIR,
        )

        tasks_db[task_id] = {
            "status": "completed",
            "srt_url": f"http://127.0.0.1:8000/timelines/{os.path.basename(timeline_files['srt_path'])}",
            "fcpxml_url": (
                f"http://127.0.0.1:8000/timelines/{os.path.basename(timeline_files['fcpxml_path'])}"
                if timeline_files.get("fcpxml_path") else None
            ),
        }
    except Exception as e:
        tasks_db[task_id] = {"status": "error", "error": str(e)}
    finally:
        _cleanup_chunks(chunks)


@router.post("/build-timeline")
def build_timeline(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    language: str = Form(default="en"),
    blocks: str = Form(default="[]"),
):
    try:
        parsed_blocks = json.loads(blocks)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Pole 'blocks' nie jest poprawnym JSON-em.")
    if not isinstance(parsed_blocks, list):
        raise HTTPException(status_code=400, detail="Pole 'blocks' musi być listą bloków.")

    ext = os.path.splitext(audio.filename or "")[1] or ".wav"
    audio_path = os.path.join(TEMP_AUDIO_DIR, f"davinci_{uuid4().hex}{ext}")
    with open(audio_path, "wb") as buffer:
        buffer.write(audio.file.read())

    # Rozwiąż postacie z DB (sesja dostępna tylko w endpoincie)
    script_sentences: List[Dict] = []
    if parsed_blocks:
        db = SessionLocal()
        try:
            script_sentences = _resolve_script_sentences_with_db(db, parsed_blocks)
        finally:
            db.close()

    if not script_sentences:
        print("[davinci] Brak skryptu — napisy powstana z samej transkrypcji Whispera.")

    task_id = uuid4().hex
    tasks_db[task_id] = {"status": "pending", "message": "Rozpoczynamy przygotowania..."}
    background_tasks.add_task(process_davinci_task, task_id, audio_path, script_sentences, language)

    return {"task_id": task_id}


def _resolve_script_sentences_with_db(db, blocks: List[Dict]) -> List[Dict]:
    """Bloki -> zdania; dane postaci (name/avatar) doładowane z DB po character_id."""
    char_cache: Dict[Any, Optional[models.Character]] = {}

    def get_character(char_id):
        if char_id is None:
            return None
        if char_id not in char_cache:
            char_cache[char_id] = db.query(models.Character).filter(models.Character.id == char_id).first()
        return char_cache[char_id]

    sentences: List[Dict] = []
    for block in blocks:
        text = (block.get("text") or "").strip()
        if not text:
            continue
        char_id = block.get("character_id")
        character = get_character(char_id) if char_id is not None else None
        for sentence_text in split_into_sentences(text):
            sentences.append({
                "text": sentence_text,
                "character_id": char_id,
                "character_name": character.name if character else None,
                "avatar_path": character.avatar_path if character else None,
                "is_narrator": char_id is None,
            })
    return sentences


@router.get("/task-status/{task_id}")
def check_task_status(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Nie znaleziono zadania w systemie")
    return tasks_db[task_id]
