from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import uuid4
import os
import json
import shutil

from db.database import get_db
from src.manager import TTSManager
from src.schemas import TTSRequest, TTSResult

router = APIRouter(
    prefix="/tts",
    tags=["tts"],
)

TEMP_AUDIO_DIR = "audiobooks/audio/temp"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

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
tts_manager.load_provider("coqui_xtts_v2")
tts_manager.load_provider("qwen_custom")
tts_manager.load_provider("qwen_design")
tts_manager.load_provider("qwen_base")
tts_manager.load_provider("omnivoice")

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
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd serwera: {str(e)}")

@router.delete("/temp")
def delete_temp_files():
    """Remove all files in the temporary audio directory."""
    clear_temp_directory()
    return {"message": "Temporary audio files deleted successfully."}


