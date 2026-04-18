from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
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
    blocks: List[AudiobookBlock]
    
    
OUTPUT_AUDIO_DIR = "audiobooks/output"
os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)

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


@router.post("/generate-audiobook")
def generate_full_audiobook(payload: AudiobookPayload, db: Session = Depends(get_db)):
    
    # 1. Tworzymy listę zadań zachowując oryginalny indeks (żeby móc to potem posortować)
    tasks = []
    for idx, block in enumerate(payload.blocks):
        tasks.append({
            "index": idx,
            "char_id": block.character_id,
            "text": block.text
        })

    # 2. INTELIGENTNE GRUPOWANIE: Sortujemy po character_id
    # Zapobiega to ciągłemu przełączaniu modeli w pamięci VRAM mikroserwisów
    tasks.sort(key=lambda x: x["char_id"] if x["char_id"] is not None else -1)

    generated_audio_files = []

    # 3. GENEROWANIE POJEDYNCZYCH PLIKÓW
    for task in tasks:
        char_id = task["char_id"]
        text = task["text"]

        if not text.strip():
            continue # Zabezpieczenie przed pustymi tekstami

        # POBIERANIE USTAWIEŃ Z TWOJEJ BAZY DANYCH

        if char_id is not None:
            
            character: Any = db.query(models.Character).filter(models.Character.id == char_id).first()
            
            if not character:
                print(f"Uwaga: Nie znaleziono postaci o ID {char_id}. Pomijam.")
                continue 
                
            # Teraz możemy używać przypisań bez żadnych kombinacji z rzutowaniem!
            provider = character.provider or "omnivoice"
            voice_path = character.voice_path
            voice_prompt = character.voice_prompt
            
            # Pobieramy JSON i upewniamy się, że to słownik
            options_dict = character.provider_options or {}
            if not isinstance(options_dict, dict):
                options_dict = {}
            
            # Zwykłe dopisanie języka
            if character.language and "language" not in options_dict:
                options_dict["language"] = character.language
        else:
            # Ustawienia dla domyślnego NARRATORA (gdy character_id jest null)
            provider = "omnivoice" 
            voice_path = None
            voice_prompt = None
            options_dict = {}

        # Przygotowanie zapytania dla Twojego TTSManager
        req = TTSRequest(
            text=text,
            provider=provider,
            voice_path=voice_path,
            voice_prompt=voice_prompt,
            options=options_dict
        )

        try:
            print(f"Generowanie bloku {task['index']} dla postaci ID: {char_id} (Model: {provider})")
            
            # Generowanie!
            result = tts_manager.generate_audio(req, provider_override=provider)
            
            # Pełna fizyczna ścieżka do utworzonego pliku temp
            # (Zakładamy, że twój TTSManager zwraca ścieżkę w result.audio_path, jeśli zwraca tylko nazwę, dodaj os.path.join)
            physical_temp_path = result.audio_path 
            
            # Upewniamy się, że to prawdziwa ścieżka systemowa, a nie URL (bo pydub potrzebuje ścieżki)
            if physical_temp_path.startswith("/audio/temp/"):
                physical_temp_path = os.path.join(TEMP_AUDIO_DIR, physical_temp_path.split("/")[-1])
            
            generated_audio_files.append((task["index"], physical_temp_path))
            
        except Exception as e:
            print(f"Błąd generowania dla bloku {task['index']}: {e}")
            raise HTTPException(status_code=500, detail=f"Błąd generowania bloku tekstu: {e}")

    # 4. PRZYWRACANIE ORYGINALNEJ KOLEJNOŚCI CHRONOLOGICZNEJ
    generated_audio_files.sort(key=lambda x: x[0])

    # 5. SCALANIE PLIKÓW W JEDEN AUDIOBOOK (Pydub)
    print("Scalanie plików audio...")
    combined_audio = AudioSegment.empty()
    
    # 600ms ciszy między kwestiami dla naturalnego flow
    silence = AudioSegment.silent(duration=600) 

    for idx, filepath in generated_audio_files:
        try:
            if os.path.exists(filepath):
                segment = AudioSegment.from_file(filepath)
                combined_audio += segment + silence
            else:
                print(f"Plik nie istnieje, pomijam scalanie: {filepath}")
        except Exception as e:
            print(f"Błąd podczas łączenia pliku {filepath}: {e}")

    # 6. ZAPIS FINALNEGO PLIKU DO KATALOGU OUTPUT
    final_filename = f"audiobook_{uuid4().hex}.wav"
    final_filepath = os.path.join(OUTPUT_AUDIO_DIR, final_filename)
    
    # Eksport do WAV (możesz też zmienić format na "mp3" jeśli zainstalowałeś kodeki w FFmpeg)
    combined_audio.export(final_filepath, format="wav")

    print(f"✅ Zakończono tworzenie audiobooka: {final_filepath}")

    # Opcjonalnie: Czyszczenie plików tymczasowych po udanym scaleniu
    # clear_temp_directory()

    return {
        "message": "Audiobook wygenerowany pomyślnie!",
        "file_url": f"http://127.0.0.1:8000/output/{final_filename}"
    }