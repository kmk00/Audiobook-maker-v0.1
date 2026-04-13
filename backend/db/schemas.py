from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime

# --- Character ---
class CharacterBase(BaseModel):
    name: str
    voice_path: str
    description: Optional[str] = None
    voice_prompt: Optional[str] = None
    avatar_path: Optional[str] = None

class CharacterCreate(CharacterBase):
    pass

class CharacterResponse(CharacterBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)