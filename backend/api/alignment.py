"""
alignment.py

Odpowiada za:
1. Transkrypcję pojedynczego chunku audio przez dedykowany worker Whisper
   (osobny kontener GPU, `worker-whisper` — patrz whisper_worker.py).
2. Dopasowanie ZNANEGO (ground-truth) tekstu chunku do rozpoznanych słów,
   żeby wyciąć dokładne timestampy dla każdego ZDANIA w obrębie tego chunku.

Kluczowe założenie: nie ufamy transkrypcji jako tekstowi (może się mylić
w słowach), tylko jako źródłu TIMINGU. Tekst do napisów zawsze bierzemy z
Twojego oryginalnego skryptu (ten, który faktycznie poszedł do TTS).

Ten moduł NIE ładuje już modelu Whisper lokalnie — woła po HTTP do
`worker-whisper`, który ma GPU i ładuje model raz przy starcie kontenera.

Wymagane zależności (u siebie, w kontenerze `api`):
    pip install requests pydub --break-system-packages
"""

import os
import re
import difflib
from typing import List, Dict, Optional

import requests
from pydub import AudioSegment

WHISPER_WORKER_URL = os.environ.get("WHISPER_WORKER_URL", "http://worker-whisper:8000")
WHISPER_REQUEST_TIMEOUT = 120  # sekund - chunk audio jest krótki, ale VAD+model potrzebuje chwili

# Kanoniczny format, do którego sprowadzamy KAŻDY plik audio (chunki TTS + cisza)
# przed pomiarem czasu i przed konkatenacją. Bez tego ffmpeg "-c copy" skleja
# pliki o różnych sample rate'ach (np. omnivoice vs qwen vs higgs) bez
# resamplingu, co powoduje drift/desync narastający w głąb pliku.
CANONICAL_SAMPLE_RATE = 44100
CANONICAL_CHANNELS = 1  # mono - standard dla audiobooków głosowych


def normalize_audio_format(audio_path: str) -> None:
    """
    Wymusza spójny sample rate i liczbę kanałów na pliku audio, nadpisując go
    w miejscu. Jeśli plik już ma poprawny format, nic nie robi (tanie sprawdzenie).

    MUSI być wołane na KAŻDYM chunku (i na pliku ciszy) PRZED:
    - pomiarem długości (get_audio_duration_seconds),
    - transkrypcją Whisperem,
    - dopisaniem do listy do konkatenacji ffmpeg.

    Inaczej zmierzone/transkrybowane czasy nie będą zgodne z tym, co faktycznie
    wyląduje w sklejonym pliku wynikowym.
    """
    audio = AudioSegment.from_file(audio_path)
    if audio.frame_rate != CANONICAL_SAMPLE_RATE or audio.channels != CANONICAL_CHANNELS:
        audio = audio.set_frame_rate(CANONICAL_SAMPLE_RATE).set_channels(CANONICAL_CHANNELS)
        audio.export(audio_path, format="wav")


def get_audio_duration_seconds(audio_path: str) -> float:
    """Dokładna długość pliku audio (do liczenia offsetów kumulacyjnych)."""
    audio = AudioSegment.from_file(audio_path)
    return len(audio) / 1000.0


def transcribe_chunk_words(audio_path: str, language: str = "en") -> List[Dict]:
    """
    Zwraca listę słów rozpoznanych przez worker Whisper w obrębie JEDNEGO
    chunku audio, z czasami WZGLĘDNYMI wobec początku tego pliku.

    [{"word": "Ludicrous", "start": 0.12, "end": 0.61}, ...]

    W razie błędu komunikacji z workerem (worker padł, timeout, itp.) zwraca
    pustą listę — alignment.py ma na to fallback (proporcjonalny podział czasu).
    """
    abs_path = os.path.abspath(audio_path)
    try:
        resp = requests.post(
            f"{WHISPER_WORKER_URL}/transcribe",
            json={"audio_path": abs_path, "language": language},
            timeout=WHISPER_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("words", [])
    except requests.exceptions.RequestException as e:
        print(f"[alignment] Nie udało się połączyć z worker-whisper ({WHISPER_WORKER_URL}): {e}")
        return []


def split_into_sentences(text: str) -> List[str]:
    """
    Dzieli tekst na zdania. Używane TYLKO do napisów (nie do generowania TTS —
    to zostaje bez zmian, jak w Twoim split_into_chunks).
    """
    sentences = re.split(r'(?<=[.!?…])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def _normalize_word(w: str) -> str:
    return re.sub(r"[^\w]", "", w).lower()


def align_sentences_to_timestamps(
    original_text: str,
    whisper_words: List[Dict],
    chunk_duration: Optional[float] = None,
) -> List[Dict]:
    """
    Dopasowuje zdania z ORYGINALNEGO tekstu chunku do timestampów Whispera.

    Zwraca listę: [{"text": "...", "start": 0.0, "end": 1.23}, ...]
    Czasy są WZGLĘDNE wobec początku chunku (offset dolicza się w tts.py).

    Jeśli Whisper nie zwrócił żadnych słów (np. cisza / błąd modelu),
    zwraca całe zdania rozłożone równomiernie na chunk_duration jako fallback.
    """
    sentences = split_into_sentences(original_text)
    if not sentences:
        return []

    if not whisper_words:
        total_chars = sum(len(s) for s in sentences) or 1
        dur = chunk_duration or 1.0
        results = []
        cursor = 0.0
        for s in sentences:
            share = (len(s) / total_chars) * dur
            results.append({"text": s, "start": cursor, "end": cursor + share})
            cursor += share
        return results

    ref_words = []
    ref_word_to_sentence = []
    for s_idx, sentence in enumerate(sentences):
        for w in sentence.split():
            ref_words.append(_normalize_word(w))
            ref_word_to_sentence.append(s_idx)

    hyp_words = [_normalize_word(w["word"]) for w in whisper_words]

    matcher = difflib.SequenceMatcher(a=ref_words, b=hyp_words, autojunk=False)
    ref_to_hyp = {}
    for block in matcher.get_matching_blocks():
        for i in range(block.size):
            ref_to_hyp[block.a + i] = block.b + i

    sentence_times: Dict[int, list] = {}
    for ref_idx, hyp_idx in ref_to_hyp.items():
        s_idx = ref_word_to_sentence[ref_idx]
        t_start = whisper_words[hyp_idx]["start"]
        t_end = whisper_words[hyp_idx]["end"]
        if s_idx not in sentence_times:
            sentence_times[s_idx] = [t_start, t_end]
        else:
            sentence_times[s_idx][0] = min(sentence_times[s_idx][0], t_start)
            sentence_times[s_idx][1] = max(sentence_times[s_idx][1], t_end)

    fallback_end = chunk_duration or (whisper_words[-1]["end"] if whisper_words else 1.0)

    results = []
    last_end = 0.0
    for s_idx, sentence in enumerate(sentences):
        if s_idx in sentence_times:
            start, end = sentence_times[s_idx]
            start = max(start, last_end)   
            end = max(end, start + 0.1)
        else:
            start = last_end
            end = min(last_end + 0.5, fallback_end)
        results.append({"text": sentence, "start": start, "end": end})
        last_end = end

    if chunk_duration and results:
        results[-1]["end"] = max(results[-1]["end"], chunk_duration)

    return results