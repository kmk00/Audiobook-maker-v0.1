
import gc
import os
from pathlib import Path
import torch
import soundfile as sf
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager

from breeze_infer.runtime import (
    load_runtime,
    resolve_device,
    set_all_seeds,
    update_generation_config_for_breeze,
)
from breeze_infer.templates import get_template, prepare_inputs
from models.fast_streaming import FastBreezeStreamingRuntime, FastStreamingConfig

MODEL_ID = "BreezeBlue/breeze-tts-2"
MODEL_DIR = os.environ.get("BREEZE_MODEL_DIR", "/models/breeze-tts-2")
MAX_NEW_TOKENS = 1500
MAX_SEQ_LEN = 2048
REPETITION_PENALTY = 1.1
DEFAULT_INSTRUCTION = "Speak clearly and naturally."

tokenizer = None
model = None
audio_tokenizer = None
runtime = None

def ensure_model_downloaded() -> str:
    if os.path.isdir(os.path.join(MODEL_DIR, ".")) and os.listdir(MODEL_DIR):
        return MODEL_DIR
    from huggingface_hub import snapshot_download
    print(f"Downloading {MODEL_ID} to {MODEL_DIR} (this may take a while)...")
    return snapshot_download(MODEL_ID, local_dir=MODEL_DIR)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Breeze TTS worker (model will be loaded lazily on first request)...")

    yield

    print("Shutting down Breeze TTS worker and clearing VRAM...")
    unload_model()

def load_model():
    global tokenizer, model, audio_tokenizer, runtime
    if runtime is not None:
        return

    device = resolve_device()
    print(f"Loading Breeze TTS 2 on {device} (this may take a moment)...")
    model_path = Path(ensure_model_downloaded())
    tokenizer, model, audio_tokenizer = load_runtime(
        model_path,
        device=device,
        attn_implementation="eager",
    )
    update_generation_config_for_breeze(model)

    config = FastStreamingConfig(
        max_new_tokens=MAX_NEW_TOKENS,
        max_seq_len=MAX_SEQ_LEN,
        fast_all=False,
        repetition_penalty=REPETITION_PENALTY,
    )
    runtime = FastBreezeStreamingRuntime(
        model, audio_tokenizer, config, tokenizer=tokenizer
    )
    print("Breeze TTS 2 model loaded successfully and ready to receive requests.")

def unload_model():
    global tokenizer, model, audio_tokenizer, runtime
    if runtime is None:
        return {"status": "unloaded", "was_loaded": False}
    tokenizer = None
    model = None
    audio_tokenizer = None
    runtime = None
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    print("Breeze TTS 2 model unloaded, VRAM cleared.")
    return {"status": "unloaded", "was_loaded": True}

app = FastAPI(title="Breeze TTS Worker", lifespan=lifespan)


class BreezeRequest(BaseModel):
    text: str
    output_path: str
    ref_audio: str | None = None
    ref_text: str | None = None
    instruction: str | None = None
    cfg_scale: float = 4.0
    seed: int = 42

@app.post("/unload")
def unload_worker():
    return unload_model()

@app.post("/generate")
def generate_audio(req: BreezeRequest):
    load_model()

    has_ref = req.ref_audio is not None and os.path.exists(req.ref_audio)
    if req.ref_audio is not None and not has_ref:
        raise HTTPException(status_code=400, detail=f"Reference audio not found: {req.ref_audio}")
    if has_ref != bool(req.ref_text and req.ref_text.strip()):
        raise HTTPException(status_code=400, detail="ref_audio and ref_text must be provided together")

    instruction = (req.instruction or "").strip() or DEFAULT_INSTRUCTION
    mode = "voice_direction/clone" if has_ref else "voice_design"
    print(f"Generating (Breeze, {mode}): {req.text[:30]}...")

    try:
        request = {
            "id": "single-request",
            "text": req.text,
            "instruction": instruction,
            "speaker": "S0",
        }
        template_name = "tts_instruction"
        if has_ref:
            request["ref_audio_path"] = req.ref_audio
            request["ref_text"] = req.ref_text.strip()
            template_name = "ref_edit_tata"

        set_all_seeds(req.seed)
        inputs = prepare_inputs(
            tokenizer,
            audio_tokenizer,
            model,
            [request],
            get_template(template_name),
            guidance_scale=req.cfg_scale,
            guidance_scale_ref=None,
            guidance_scale_ins=None,
        )

        os.makedirs(os.path.dirname(req.output_path) or ".", exist_ok=True)
        with sf.SoundFile(
            req.output_path,
            mode="w",
            samplerate=runtime.sample_rate,
            channels=1,
            subtype="PCM_16",
        ) as output_file:
            for chunk in runtime.iter_audio_chunks(inputs, request_id="single-request"):
                output_file.write(chunk.audio)

        print(f"Audio generated and saved to: {req.output_path}")
        return {"status": "success", "file": req.output_path}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
