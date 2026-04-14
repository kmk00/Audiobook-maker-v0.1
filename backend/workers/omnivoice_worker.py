
import os
import torch
import soundfile as sf
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from omnivoice import OmniVoice

model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    print("Starting OmniVoice worker...")
    
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    if torch.backends.mps.is_available():
        device = "mps"
        
    print(f"Loading OmniVoice weights on {device} (this may take a moment)...")
    model = OmniVoice.from_pretrained(
        "k2-fsa/OmniVoice",
        device_map=device,
        dtype=torch.float16
    )
    print("OmniVoice model loaded successfully and ready to receive requests.")
    
    yield
    
    print("Shutting down OmniVoice worker and clearing VRAM...")
    if model is not None:
        del model
        torch.cuda.empty_cache()

app = FastAPI(title="OmniVoice Worker", lifespan=lifespan)


class OmniRequest(BaseModel):
    text: str
    output_path: str
    voice_prompt: str | None = None
    voice_path: str | None = None
    ref_text: str | None = None
    speed: float = 1.0

@app.post("/generate")
def generate_audio(req: OmniRequest):
    global model
    if model is None:
        raise HTTPException(status_code=503, detail="Model is loading.")

    print(f"Generating (OmniVoice): {req.text[:30]}...")

    try:
        
        if req.voice_path and os.path.exists(req.voice_path):
            print("Voice cloning mode detected.")
            audio = model.generate(
                text=req.text,
                ref_audio=req.voice_path,
                ref_text=req.ref_text, 
                speed=req.speed
            )
        
        elif req.voice_prompt:
            print("Voice design mode detected.")
            audio = model.generate(
                text=req.text,
                instruct=req.voice_prompt,
                speed=req.speed
            )
        
        else:
            print("Auto voice mode detected.")
            audio = model.generate(
                text=req.text,
                speed=req.speed
            )

        
        sf.write(req.output_path, audio[0], 24000)
        print(f"Audio generated and saved to: {req.output_path}")
        return {"status": "success", "file": req.output_path}
        
    except Exception as e:
        print(f"Error generating audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))