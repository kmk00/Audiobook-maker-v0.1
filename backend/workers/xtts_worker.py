import os
import torch
import torchaudio
import soundfile as sf
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from TTS.api import TTS

# --- PATCHE DLA PYTORCH 2.6 ---
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    kwargs.setdefault("weights_only", False)
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

def _patched_torchaudio_load(filepath, *args, **kwargs):
    data, sample_rate = sf.read(filepath, dtype="float32", always_2d=True)
    return torch.tensor(data.T), sample_rate
torchaudio.load = _patched_torchaudio_load
# -----------------------------------------------------------------------

app = FastAPI(title="XTTS v2 Worker")
model = None

class GenerationRequest(BaseModel):
    text: str
    voice_path: str
    language: str = "en" 
    output_path: str
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    print("Loading XTTS model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading model on {device}...")
    model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    print("XTTS model loaded successfully")
    
    yield 
    

    print("Shutting down XTTS worker and freeing GPU memory...")
    if model is not None:
        del model
        torch.cuda.empty_cache()
        print("XTTS worker shutdown complete, GPU memory freed.")


app = FastAPI(title="XTTS v2 Worker", lifespan=lifespan)
    
@app.post("/generate")
def generate_audio(request: GenerationRequest):
    global model
    
    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded.")
    
    if not os.path.exists(request.voice_path):
        raise HTTPException(status_code=400, detail="Voice file not found.")
    
    try:
        print(f"[XTTS Worker] Generating audio for text: '{request.text}' with voice: '{request.voice_path}'")
        model.tts_to_file(
            text=request.text,
            speaker_wav=request.voice_path,
            language=request.language,
            file_path=request.output_path
        )
        print(f"[XTTS Worker] Audio generated and saved to: {request.output_path}")
        return {"message": "Audio generated successfully.", "output_path": request.output_path}
    except Exception as e:
        print(f"[XTTS Worker] Error during audio generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
