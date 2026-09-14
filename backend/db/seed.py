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
            "name": "OmniVoice - Generic", 
            "provider": "omnivoice",
            "description": "OmniVoice with path, no prompt",
            "avatar_path": None,
            "voice_prompt": None,
            "voice_path": "tests/voice_samples/male.wav",
        },
        {
            "name": "OmniVoice - Generic", 
            "provider": "omnivoice",
            "description": "OmniVoice without path, with prompt",
            "voice_prompt": "male, slow",
            "voice_path": None,
        },
        {
            "name": "OmniVoice - Generic", 
            "provider": "omnivoice",
            "description": "OmniVoice with path, with prompt",
            "avatar_path": None,
            "voice_prompt": "male, slow",
            "voice_path": "tests/voice_samples/male.wav",
        },
    ]

    for data in dummy_characters:
        char = Character(
            name=data["name"],
            provider=data["provider"], 
            description=data.get("description", None),
            voice_path=data.get("voice_path", None),
            avatar_path=data.get("avatar_path", None), 
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