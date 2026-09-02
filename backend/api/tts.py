import re
import subprocess
from typing import Any, List, Optional
import traceback
from .alignment import (
    get_audio_duration_seconds,
    normalize_audio_format,
    transcribe_chunk_words,
    align_sentences_to_timestamps,
)
from .timeline_export import export_all

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import uuid4
import os
import json
import shutil
from pydub import AudioSegment
from db import models

from db.database import get_db
from src.manager import TTSManager
from src.schemas import TTSRequest, TTSResult

router = APIRouter(
    prefix="/tts",
    tags=["tts"],
)
class AudiobookBlock(BaseModel):
    character_id: Optional[int]
    text: str

class AudiobookPayload(BaseModel):
    mode: str
    generate_timeline: bool = True
    blocks: List[AudiobookBlock]
    
    
    
    
OUTPUT_AUDIO_DIR = "audiobooks/output"
os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)

TEMP_AUDIO_DIR = "audiobooks/audio/temp"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

TIMELINE_OUTPUT_DIR = "audiobooks/timelines"
os.makedirs(TIMELINE_OUTPUT_DIR, exist_ok=True)

NAMEPLATE_CACHE_DIR = "audiobooks/nameplates"
os.makedirs(NAMEPLATE_CACHE_DIR, exist_ok=True)
tasks_db = {}

def clear_temp_directory():
    """Remove all files in the temporary audio directory."""
    if os.path.exists(TEMP_AUDIO_DIR):
        for filename in os.listdir(TEMP_AUDIO_DIR):
            file_path = os.path.join(TEMP_AUDIO_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                pass

tts_manager = TTSManager(output_dir=TEMP_AUDIO_DIR)
tts_manager.load_provider("omnivoice")

def split_into_chunks(text: str, max_chars: int = 1200) -> List[str]:
    """Tnie tekst na zgrabne paczki bez ucinania zdań wpół."""
    sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence: continue

        if len(current_chunk) + len(sentence) <= max_chars:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            if len(sentence) > max_chars:
                for i in range(0, len(sentence), max_chars):
                    chunks.append(sentence[i:i+max_chars])
                current_chunk = ""
            else:
                current_chunk = sentence + " "
                
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks

@router.post("/generate", response_model=TTSResult)
def generate_speech(
    text: str = Form(...),
    provider: str = Form(...),
    options: str = Form(default="{}"),
    voiceToClone: UploadFile = File(None),
    db: Session = Depends(get_db)
):

    try:
        parsed_options = json.loads(options)
    except json.JSONDecodeError:
        parsed_options = {}

    clear_temp_directory()

    temp_ref_path = None
    if voiceToClone:
        temp_ref_filename = f"ref_{uuid4().hex}_{voiceToClone.filename}"
        temp_ref_path = os.path.join(TEMP_AUDIO_DIR, temp_ref_filename)
        with open(temp_ref_path, "wb") as buffer:
            shutil.copyfileobj(voiceToClone.file, buffer)

    request = TTSRequest(
        text=text,
        provider=provider,
        voice_path=temp_ref_path,
        voice_prompt=parsed_options.get("voicePrompt", None),
        options=parsed_options
    )
    
    print(f"Generating audio for text: '{request.text}' with model: '{provider}'")

    try:
        result = tts_manager.generate_audio(request, provider_override=provider)
        filename = os.path.basename(result.audio_path)
        result.audio_path = f"/audio/temp/{filename}"
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        print(f"[tts/generate] RuntimeError: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print(f"[tts/generate] Unexpected error:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Błąd serwera: {str(e)}")

@router.delete("/temp")
def delete_temp_files():
    """Remove all files in the temporary audio directory."""
    clear_temp_directory()
    return {"message": "Temporary audio files deleted successfully."}


@router.post("/generate-audiobook")
def start_audiobook_generation(
    payload: AudiobookPayload, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    task_id = uuid4().hex
    

    tasks = []
    for block_idx, block in enumerate(payload.blocks):
        text = block.text.strip()
        if not text: continue
            
        chunks = split_into_chunks(text, max_chars=1200)
        for chunk_idx, chunk_text in enumerate(chunks):
            tasks.append({
                "global_index": (block_idx, chunk_idx),
                "char_id": block.character_id,
                "text": chunk_text
            })


    tasks.sort(key=lambda x: x["char_id"] if x["char_id"] is not None else -1)


    prepared_tasks = []
    for task in tasks:
        char_id = task["char_id"]
        
        if char_id is not None:
            character: Any = db.query(models.Character).filter(models.Character.id == char_id).first()
            if not character: continue 
                
            provider = character.provider or "omnivoice"
            voice_path = character.voice_path
            voice_prompt = character.voice_prompt
            
            options_dict = character.provider_options or {}
            if not isinstance(options_dict, dict): options_dict = {}
            if character.language and "language" not in options_dict:
                options_dict["language"] = character.language
        else:
            provider = "omnivoice" 
            voice_path = None
            voice_prompt = None
            options_dict = {}

        prepared_tasks.append({
            "global_index": task["global_index"],
            "provider": provider,
            "voice_path": voice_path,
            "voice_prompt": voice_prompt,
            "options": options_dict,
            "text": task["text"],
            "character_id": char_id,
            "character_name": character.name if char_id is not None else None,
            "avatar_path": (
                os.path.abspath(character.avatar_path)
                if char_id is not None and character.avatar_path else None
            ),
        })


    tasks_db[task_id] = {"status": "pending", "message": "Rozpoczynamy przygotowania..."}
    background_tasks.add_task(process_audiobook_task, task_id, prepared_tasks, payload.generate_timeline)

    return {"task_id": task_id}


@router.get("/task-status/{task_id}")
def check_task_status(task_id: str):
    """Odpytywane przez Vue co kilka sekund, by sprawdzić postęp."""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Nie znaleziono zadania w systemie")
    return tasks_db[task_id]
    

def process_audiobook_task(task_id: str, prepared_tasks: list, generate_timeline: bool = True):
    try:
        # --- 1. PRZYGOTOWANIE CISZY I POMIAR JEJ DOKŁADNEGO CZASU ---
        silence_path = os.path.abspath(os.path.join(TEMP_AUDIO_DIR, "silence_600ms.wav")).replace("\\", "/")
        if not os.path.exists(silence_path):
            AudioSegment.silent(duration=600).export(silence_path, format="wav")
        
        normalize_audio_format(silence_path)
        
        # Zamiast zgadywać (0.6), mierzymy dokładny czas pliku, który FFmpeg fizycznie połączy
        EXACT_SILENCE_DURATION = get_audio_duration_seconds(silence_path)
        print(f"[audiobook] Dokładny zmierzony czas ciszy: {EXACT_SILENCE_DURATION:.4f}s")

        tasks_db[task_id] = {"status": "processing", "message": f"Generowanie paczek audio (0/{len(prepared_tasks)})..."}
        generated_audio_files = []
        task_lookup = {t["global_index"]: t for t in prepared_tasks}

        for i, task_data in enumerate(prepared_tasks):
            req = TTSRequest(
                text=task_data["text"],
                provider=task_data["provider"],
                voice_path=task_data["voice_path"],
                voice_prompt=task_data["voice_prompt"],
                options=task_data["options"]
            )
            tasks_db[task_id] = {
                "status": "processing",
                "message": f"Wygenerowano {i + 1}/{len(prepared_tasks)} fragmentów..."
            }
            result = tts_manager.generate_audio(req, provider_override=task_data["provider"])
            phys_path = result.audio_path
            if phys_path.startswith("/audio/temp/"):
                phys_path = os.path.join(TEMP_AUDIO_DIR, phys_path.split("/")[-1])
                
            normalize_audio_format(phys_path)
            generated_audio_files.append((task_data["global_index"], phys_path))

        generated_audio_files.sort(key=lambda x: x[0])

        all_segments = []

        # --- 2. GENEROWANIE TIMELINU (Z UŻYCIEM DOKŁADNEGO CZASU) ---
        if generate_timeline:
            tasks_db[task_id] = {"status": "processing", "message": "Analiza timingu (Whisper)..."}
            cumulative_time = 0.0
            # USUNIĘTO: SILENCE_GAP = 0.6

            for idx, (global_index, phys_path) in enumerate(generated_audio_files):
                task_data = task_lookup[global_index]
                chunk_duration = get_audio_duration_seconds(phys_path)

                try:
                    whisper_words = transcribe_chunk_words(phys_path, language="en")
                except Exception as whisper_err:
                    print(f"[audiobook] Whisper nie powiódł się dla {phys_path}: {whisper_err}")
                    whisper_words = []

                aligned_sentences = align_sentences_to_timestamps(
                    original_text=task_data["text"],
                    whisper_words=whisper_words,
                    chunk_duration=chunk_duration,
                )

                for sentence in aligned_sentences:
                    all_segments.append({
                        "start": cumulative_time + sentence["start"],
                        "end": cumulative_time + sentence["end"],
                        "text": sentence["text"],
                        "character_id": task_data["character_id"],
                        "character_name": task_data["character_name"],
                        "avatar_path": task_data["avatar_path"],
                        "is_narrator": task_data["character_id"] is None,
                    })

                if idx < len(generated_audio_files) - 1:
                    # ZAMIAST: cumulative_time += chunk_duration + SILENCE_GAP
                    cumulative_time += chunk_duration + EXACT_SILENCE_DURATION
                else:
                    cumulative_time += chunk_duration

        # --- 3. SKALANIE AUDIO PRZEZ FFMPEG ---
        tasks_db[task_id] = {"status": "processing", "message": "Trwa błyskawiczne scalanie plików bez zużycia RAM-u..."}

        concat_file_path = os.path.join(TEMP_AUDIO_DIR, f"concat_{task_id}.txt")
        with open(concat_file_path, "w", encoding="utf-8") as f:
            for _, filepath in generated_audio_files:
                abs_filepath = os.path.abspath(filepath).replace("\\", "/")
                f.write(f"file '{abs_filepath}'\n")
                f.write(f"file '{silence_path}'\n")

        final_filename = f"audiobook_{task_id}.wav"
        final_filepath = os.path.join(OUTPUT_AUDIO_DIR, final_filename)

        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file_path, "-c", "copy", final_filepath
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        file_url = f"http://127.0.0.1:8000/output/{final_filename}"
        result_status = {"status": "completed", "file_url": file_url, "srt_url": None, "fcpxml_url": None}

        if generate_timeline and all_segments:
            tasks_db[task_id] = {"status": "processing", "message": "Generowanie plików do DaVinci (SRT + FCPXML)..."}
            timeline_files = export_all(
                segments=all_segments,
                output_dir=TIMELINE_OUTPUT_DIR,
                task_id=task_id,
                nameplate_cache_dir=NAMEPLATE_CACHE_DIR,
            )
            srt_filename = os.path.basename(timeline_files["srt_path"])
            result_status["srt_url"] = f"http://127.0.0.1:8000/timelines/{srt_filename}"

            if timeline_files.get("fcpxml_path"):
                fcpxml_filename = os.path.basename(timeline_files["fcpxml_path"])
                result_status["fcpxml_url"] = f"http://127.0.0.1:8000/timelines/{fcpxml_filename}"

        tasks_db[task_id] = result_status

    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode('utf-8', errors='ignore')
        tasks_db[task_id] = {"status": "error", "error": f"Błąd scalania FFmpeg: {error_output}"}
    except Exception as e:
        tasks_db[task_id] = {"status": "error", "error": str(e)}