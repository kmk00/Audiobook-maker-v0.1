from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import shutil

from db.database import get_db
from db.models import Character
from db.schemas import CharacterCreate, CharacterResponse, CharacterUpdate

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
def create_character(character: CharacterCreate, db: Session = Depends(get_db)):
    
    if db.query(Character).filter(Character.name == character.name).first():
        raise HTTPException(status_code=400, detail="Character already exists")

    db_character = Character(**character.model_dump())
    db.add(db_character)
    db.flush()
    
    safe_name = db_character.name.replace(" ", "_").lower()
    folder_path = f"characters/{db_character.id}_{safe_name}"
    os.makedirs(folder_path, exist_ok=True)
    
    db.commit()
    db.refresh(db_character)
    return db_character

@router.delete("/{character_id}")
def delete_single_character(character_id: int, db: Session = Depends(get_db)):
    character = db.query(Character).filter(Character.id == character_id).first()
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
        
    safe_name = character.name.replace(" ", "_").lower()
    folder_path = f"characters/{character.id}_{safe_name}"
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
def update_character(character_id: int, character_update: CharacterUpdate, db: Session = Depends(get_db)):
    
    db_character = db.query(Character).filter(Character.id == character_id).first()
    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")


    if character_update.name and character_update.name != db_character.name:
        existing = db.query(Character).filter(Character.name == character_update.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Character with this name already exists")
            
        old_safe_name = db_character.name.replace(" ", "_").lower()
        old_folder_path = f"characters/{db_character.id}_{old_safe_name}"
        
        new_safe_name = character_update.name.replace(" ", "_").lower()
        new_folder_path = f"characters/{db_character.id}_{new_safe_name}"
        
        if os.path.exists(old_folder_path):
            os.rename(old_folder_path, new_folder_path)


    update_data = character_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_character, key, value)

    db.commit()
    db.refresh(db_character)
    return db_character