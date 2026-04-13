from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os
import shutil

from db.database import get_db
from db.models import Character

router = APIRouter(
    prefix="/characters",
    tags=["characters"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
def get_characters(db: Session = Depends(get_db)):
    
    characters = db.query(Character).all()
    
    if not characters:
        raise HTTPException(status_code=404, detail="Characters not found")
    
    return characters

@router.post("/")
def create_character(character: Character, db: Session = Depends(get_db)):
    
    if db.query(Character).filter(Character.name == character.name).first():
        raise HTTPException(status_code=400, detail="Character already exists")
    
    
    db_character = Character(**character.dict())
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character


@router.delete("/")
def delete_characters(db: Session = Depends(get_db)):
    
    if not db.query(Character).all():
        raise HTTPException(status_code=404, detail="Characters not found")
    
    db.query(Character).delete()
    db.commit()
    
    shutil.rmtree('../characters')
    os.makedirs('../characters',exist_ok=True)
    return

