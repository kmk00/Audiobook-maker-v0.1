import os
import torch
import soundfile as sf
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from qwen_tts import Qwen3TTSModel

model = None
current_model_id = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    global model
    if model is not None:
        del model
        torch.cuda.empty_cache()
        print("VRAM cleaned up on shutdown.")

app = FastAPI(title="Qwen3 Worker", lifespan=lifespan)

class QwenRequest(BaseModel):
    model_id: str
    text: str
    output_path: str
    language: str = "Auto"
    voice_prompt: str | None = None
    voice_path: str | None = None
    ref_text: str | None = None
    speaker: str | None = None

@app.post("/generate")
def generate_audio(req: QwenRequest):
    global model, current_model_id
    

    if model is None or current_model_id != req.model_id:
        print(f"    Loading model '{req.model_id}'...")
        if model is not None:
            del model
            torch.cuda.empty_cache()
            
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        model = Qwen3TTSModel.from_pretrained(req.model_id, device_map=device, dtype=torch.bfloat16)
        current_model_id = req.model_id
        print(f"    Model '{req.model_id}' loaded successfully on device '{device}'.")

    try:
        if "VoiceDesign" in req.model_id:
            wavs, sr = model.generate_voice_design(text=req.text, language=req.language, instruct=req.voice_prompt or "")
        elif "CustomVoice" in req.model_id:
            wavs, sr = model.generate_custom_voice(text=req.text, language=req.language, speaker=req.speaker or "Vivian", instruct=req.voice_prompt or "")
        elif "Base" in req.model_id:
            wavs, sr = model.generate_voice_clone(text=req.text, language=req.language, ref_audio=req.voice_path, ref_text=req.ref_text)
        else:
            raise ValueError(f"Nieznany model: {req.model_id}")

        sf.write(req.output_path, wavs[0], sr)
        return {"status": "success", "file": req.output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))