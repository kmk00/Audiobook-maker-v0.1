from fastapi import APIRouter, Depends, HTTPException
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
    

    db_character.voice_dir = folder_path 
    
    db.commit()
    db.refresh(db_character)
    return db_character

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