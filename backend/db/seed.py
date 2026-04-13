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
            "description": "Lektor Domyślny",
            "voice_path": "lektor.mp3",
            "avatar_path": "lektor.jpg",
            "voice_prompt": "Spokojny, głęboki męski głos idealny do narracji."
        },
        {
            "name": "Młoda Bohaterka",
            "voice_path": "Emmy.mp3",
            "avatar_path": "Emmy.jpg",
        },
        {
            "name": "Mroczny Złoczyńca", 
            "description": "Niski, powolny i chropowaty głos.",
        }
    ]

    for data in dummy_characters:

        char = Character(
            name=data["name"],
            description=data.get("description", None),
            voice_path=data.get("voice_path", "default_voice.mp3"),
            avatar_path=data.get("avatar_path", "default_avatar.jpg"),
            voice_prompt=data.get("voice_prompt", None),
            
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