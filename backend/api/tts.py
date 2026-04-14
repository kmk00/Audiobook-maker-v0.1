from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
import os

from db.database import get_db
from db.models import Character
from src.manager import TTSManager
from src.schemas import TTSRequest, TTSResult

router = APIRouter(
    prefix="/tts",
    tags=["tts"],
)

tts_manager = TTSManager(output_dir="audiobooks/audio")
tts_manager.load_provider("coqui_xtts_v2")
tts_manager.load_provider("qwen_custom")
tts_manager.load_provider("qwen_design")
tts_manager.load_provider("qwen_base")
tts_manager.load_provider("omnivoice")

@router.post("/generate", response_model=TTSResult)
def generate_speech(request: TTSRequest, db: Session = Depends(get_db)):
    
    if request.voice_id:
        character = db.query(Character).filter(Character.id == request.voice_id).first()
        if not character:
            raise HTTPException(status_code=404, detail=f"Character with ID {request.voice_id} not found.")
        
        
        request.voice_path = character.voice_path # type: ignore
        request.voice_prompt = character.voice_prompt # type: ignore
        
        request.provider = character.provider  # type: ignore
        print(f"Using character '{character.name}' with provider '{character.provider}' for TTS generation.")

    
    output_filename = f"{uuid4().hex}.wav"
    output_path = os.path.join(tts_manager.output_dir, output_filename)

    
    try:
        provider = tts_manager._providers.get(request.provider) # type: ignore
        if not provider:
            raise ValueError(f"Provider '{request.provider}' nie jest obsługiwany.")
            
        result = provider.generate(request, output_path)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd serwera: {str(e)}")