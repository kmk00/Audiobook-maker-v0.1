import re
import subprocess
from typing import Any, List, Optional

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
    blocks: List[AudiobookBlock]
    
    
OUTPUT_AUDIO_DIR = "audiobooks/output"
os.makedirs(OUTPUT_AUDIO_DIR, exist_ok=True)

TEMP_AUDIO_DIR = "audiobooks/audio/temp"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

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
tts_manager.load_provider("coqui_xtts_v2")
tts_manager.load_provider("qwen_custom")
tts_manager.load_provider("qwen_design")
tts_manager.load_provider("qwen_base")
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
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
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
            "text": task["text"]
        })


    tasks_db[task_id] = {"status": "pending", "message": "Rozpoczynamy przygotowania..."}
    background_tasks.add_task(process_audiobook_task, task_id, prepared_tasks)

    return {"task_id": task_id}


@router.get("/task-status/{task_id}")
def check_task_status(task_id: str):
    """Odpytywane przez Vue co kilka sekund, by sprawdzić postęp."""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Nie znaleziono zadania w systemie")
    return tasks_db[task_id]
    

def process_audiobook_task(task_id: str, prepared_tasks: list):
    try:
        tasks_db[task_id] = {"status": "processing", "message": f"Generowanie paczek audio (0/{len(prepared_tasks)})..."}
        generated_audio_files = []


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
            
            generated_audio_files.append((task_data["global_index"], phys_path))


        generated_audio_files.sort(key=lambda x: x[0])
        tasks_db[task_id] = {"status": "processing", "message": "Trwa błyskawiczne scalanie plików bez zużycia RAM-u..."}


        silence_path = os.path.abspath(os.path.join(TEMP_AUDIO_DIR, "silence_600ms.wav")).replace("\\", "/")
        if not os.path.exists(silence_path):
            AudioSegment.silent(duration=600).export(silence_path, format="wav")


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
        tasks_db[task_id] = {"status": "completed", "file_url": file_url}

    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode('utf-8', errors='ignore')
        tasks_db[task_id] = {"status": "error", "error": f"Błąd scalania FFmpeg: {error_output}"}
    except Exception as e:
        tasks_db[task_id] = {"status": "error", "error": str(e)}