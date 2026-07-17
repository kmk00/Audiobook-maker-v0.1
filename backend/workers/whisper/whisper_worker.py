"""
whisper_worker.py

Dedykowany worker GPU dla transkrypcji Whisper (word-level timestamps).
Model ładowany RAZ przy starcie kontenera (tak jak Twoje worker'y TTS ładują
modele przy starcie), a nie przy każdym zapytaniu.

Kontrakt HTTP:
    POST /transcribe
    body: {"audio_path": "audiobooks/audio/temp/xxx.wav", "language": "en"}
    response: {"words": [{"word": "Hello", "start": 0.12, "end": 0.45}, ...]}

    GET /health -> {"status": "ok", "model": "medium"}

Zakłada, że ten kontener ma zamontowany ten sam wolumen ./backend:/app co
kontener `api` — dzięki temu ścieżki do plików audio są identyczne po obu
stronach i nie trzeba przesyłać samych bajtów audio przez HTTP.
"""

import os
from typing import List, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from faster_whisper import WhisperModel

MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "medium")
DEVICE = os.environ.get("WHISPER_DEVICE", "cuda")
COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "float16")

app = FastAPI(title="Whisper Alignment Worker")

print(f"[whisper_worker] Ładowanie modelu '{MODEL_SIZE}' na {DEVICE} ({COMPUTE_TYPE})...")
model = WhisperModel(MODEL_SIZE, device=DEVICE, compute_type=COMPUTE_TYPE)
print("[whisper_worker] Model załadowany, gotowy do pracy.")


class TranscribeRequest(BaseModel):
    audio_path: str
    language: str = "en"


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_SIZE, "device": DEVICE}


@app.post("/transcribe")
def transcribe(req: TranscribeRequest) -> Dict[str, List[Dict]]:
    abs_path = os.path.abspath(req.audio_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail=f"Plik audio nie istnieje w kontenerze workera: {abs_path}")

    try:
        segments, _info = model.transcribe(
            abs_path,
            word_timestamps=True,
            language=req.language,
            vad_filter=True,
        )
        words = []
        for segment in segments:
            if not segment.words:
                continue
            for w in segment.words:
                words.append({"word": w.word.strip(), "start": w.start, "end": w.end})
        return {"words": words}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd transkrypcji: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)