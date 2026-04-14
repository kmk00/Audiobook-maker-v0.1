import os
from sqlalchemy.orm import Session
from db.database import SessionLocal, engine, Base
from db.models import Character
import shutil

def seed_characters():
    db: Session = SessionLocal()
    
    print("Removing old data...")
    db.query(Character).delete()
    db.commit()
    
    characters_base_dir = "characters"
    if os.path.exists(characters_base_dir):
        shutil.rmtree(characters_base_dir)
        print("  -> Removed old characters folder")

    print("Creating characters folder...")
    os.makedirs(characters_base_dir, exist_ok=True)

    print("Seeding characters...")
    dummy_characters = [
        {
            "name": "Lektor", 
            "provider": "coqui_xtts_v2", # Lektor będzie zawsze używał klonowania w XTTS
            "description": "Lektor Domyślny - idealny do czytania książek.",
            "voice_prompt": ""
        },
        {
            "name": "Młoda Bohaterka",
            "provider": "qwen_design", # Bohaterka będzie tworzona opisem przez Qwena
            "description": "Energiczny, młody głos kobiecy.",
            "voice_prompt": "female, young, high energy, clear voice, cheerful"
        },
        {
            "name": "Mroczny Złoczyńca", 
            "provider": "omnivoice", # Złoczyńca będzie tworzony opisem przez OmniVoice
            "description": "Niski, powolny i chropowaty głos.",
            "voice_prompt": "male, low pitch, raspy, slow speaking rate, serious, dark"
        }
    ]

    for data in dummy_characters:
        char = Character(
            name=data["name"],
            provider=data["provider"], # <--- Dodajemy przypisanie przy tworzeniu
            description=data.get("description", ""),
            voice_path="",  
            avatar_path="", 
            voice_prompt=data.get("voice_prompt", ""),
        )
        db.add(char)
        db.flush() 
        

        safe_name = char.name.replace(" ", "_").lower()
        folder_path = f"{characters_base_dir}/{safe_name}_{char.id}"
        
        os.makedirs(folder_path, exist_ok=True)
        print(f"  -> Added character: {char.name} (Folder: {folder_path})")

    db.commit()
    db.close()
    print("Seeding done.")

if __name__ == "__main__":
    print("Checking database...")
    Base.metadata.create_all(bind=engine)
    
    seed_characters()