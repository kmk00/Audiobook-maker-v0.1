import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, UploadFile
from sqlalchemy.orm import Session
import os
import shutil

from db.database import get_db
from db.models import Character
from db.schemas import CharacterCreate, CharacterResponse

router = APIRouter(
    prefix="/characters",
    tags=["characters"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=list[CharacterResponse])
def get_characters(db: Session = Depends(get_db)):
    characters = db.query(Character).all()
    
    if not characters:
        raise HTTPException(status_code=404, detail="Characters not found")
    
    return characters

@router.get("/{character_id}", response_model=CharacterResponse)
def get_single_character(character_id: int, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return character



@router.post("/", response_model=CharacterResponse)
def create_character(name: str = Form(...),
    provider: str = Form(...),
    description: str = Form(None),
    voice_prompt: str = Form(None),
    language: str = Form(None),                    
    provider_options: str = Form(default="{}"),    
    temp_preview_path: str = Form(None), 
    category: str = Form(None),
    tags: str = Form(default="[]"),
    voice_file: UploadFile = File(None),
    avatar_file: UploadFile = File(None),
    db: Session = Depends(get_db)):
    if db.query(Character).filter(Character.name == name).first():
        raise HTTPException(status_code=400, detail="Character already exists")

    try:
        parsed_options = json.loads(provider_options)
    except json.JSONDecodeError:
        parsed_options = {}
        
    try:
        parsed_tags = json.loads(tags)
        if not isinstance(parsed_tags, list):
            parsed_tags = []
    except json.JSONDecodeError:
        parsed_tags = []

    db_character = Character(
        name=name,
        provider=provider,
        description=description,
        voice_prompt=voice_prompt,
        language=language,
        provider_options=parsed_options,
        category=category,
        tags=parsed_tags,
        voice_path="",
        avatar_path="",
        preview_path=""
    )
    db.add(db_character)
    db.flush() 
    
    safe_name = db_character.name.replace(" ", "_").lower()
    folder_path = f"characters/{safe_name}_{db_character.id}"
    os.makedirs(folder_path, exist_ok=True)
    
    if voice_file:
        # Safeguard against missing filename and ensure we don't have path traversal issues
        safe_filename = voice_file.filename or ""
        file_extension = os.path.splitext(safe_filename)[1]
        voice_path = f"{folder_path}/voice{file_extension}"
        with open(voice_path, "wb") as buffer:
            shutil.copyfileobj(voice_file.file, buffer)
        db_character.voice_path = voice_path # type: ignore


    if avatar_file:
        # Safeguard against missing filename and ensure we don't have path traversal issues
        safe_filename = avatar_file.filename or ""
        avatar_extension = os.path.splitext(safe_filename)[1]
        avatar_path = f"{folder_path}/avatar{avatar_extension}"
        with open(avatar_path, "wb") as buffer:
            shutil.copyfileobj(avatar_file.file, buffer)
        db_character.avatar_path = avatar_path # type: ignore

    if temp_preview_path:
        local_temp_path = temp_preview_path.replace("/audio/", "audiobooks/audio/")
        if os.path.exists(local_temp_path):
            final_preview_path = f"{folder_path}/preview.wav"
            shutil.move(local_temp_path, final_preview_path)
            db_character.preview_path = final_preview_path # type: ignore
    
    temp_dir = "audiobooks/audio/temp"
    if os.path.exists(temp_dir):
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception:
                pass 
    
    

    db.commit()
    db.refresh(db_character)
    return db_character






# @router.post("/", response_model=CharacterResponse)
# def create_character(character: CharacterCreate, db: Session = Depends(get_db)):
    
#     if db.query(Character).filter(Character.name == character.name).first():
#         raise HTTPException(status_code=400, detail="Character already exists")

#     db_character = Character(**character.model_dump())
#     db.add(db_character)
#     db.flush()
    
#     safe_name = db_character.name.replace(" ", "_").lower()
#     folder_path = f"characters/{db_character.id}_{safe_name}"
#     os.makedirs(folder_path, exist_ok=True)
    
#     db.commit()
#     db.refresh(db_character)
#     return db_character

@router.delete("/{character_id}")
def delete_single_character(character_id: int, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
        
    safe_name = character.name.replace(" ", "_").lower()
    folder_path = f"characters/{safe_name}_{character.id}" 
    
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        
    db.delete(character)
    db.commit()
    return {"detail": f"Character {character_id} deleted successfully."}

@router.delete("/")
def delete_characters(db: Session = Depends(get_db)):
    if not db.query(Character).all():
        raise HTTPException(status_code=404, detail="Characters not found")
    
    db.query(Character).delete()
    db.commit()
    
    base_dir = 'characters'
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir, exist_ok=True)
    
    return {"detail": "Wszystkie postacie i ich foldery zostały pomyślnie usunięte."}

@router.put("/{character_id}", response_model=CharacterResponse)
def update_character(character_id: int,
    name: str = Form(None),
    avatar_file: UploadFile = File(None),
    db: Session = Depends(get_db)):

    db_character = db.query(Character).filter(Character.id == character_id).first()
    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")

    if name and name != db_character.name:
        existing = db.query(Character).filter(Character.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Character with this name already exists")

        old_safe_name = db_character.name.replace(" ", "_").lower()
        old_folder_path = f"characters/{old_safe_name}_{db_character.id}"

        new_safe_name = name.replace(" ", "_").lower()
        new_folder_path = f"characters/{new_safe_name}_{db_character.id}"

        if os.path.exists(old_folder_path):
            os.rename(old_folder_path, new_folder_path)
            # Keep stored file paths pointing at the renamed folder
            for field in ("voice_path", "avatar_path", "preview_path"):
                old_path = getattr(db_character, field, None)
                if old_path and old_path.startswith(old_folder_path):
                    setattr(db_character, field, old_path.replace(old_folder_path, new_folder_path, 1))

        db_character.name = name # type: ignore

    folder_path = f"characters/{db_character.name.replace(' ', '_').lower()}_{db_character.id}"

    if avatar_file:
        # Safeguard against missing filename and ensure we don't have path traversal issues
        safe_filename = avatar_file.filename or ""
        avatar_extension = os.path.splitext(safe_filename)[1]
        new_avatar_path = f"{folder_path}/avatar{avatar_extension}"
        os.makedirs(folder_path, exist_ok=True)
        with open(new_avatar_path, "wb") as buffer:
            shutil.copyfileobj(avatar_file.file, buffer)

        # Remove the old avatar file if it differs from the new one
        old_avatar_path = db_character.avatar_path
        if old_avatar_path and old_avatar_path != new_avatar_path and os.path.exists(old_avatar_path):
            try:
                os.remove(old_avatar_path)
            except OSError:
                pass

        db_character.avatar_path = new_avatar_path # type: ignore

    db.commit()
    db.refresh(db_character)
    return db_character