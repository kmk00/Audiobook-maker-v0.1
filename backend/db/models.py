from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import relationship
from db.database import Base

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    provider = Column(String)
    
    description = Column(String, nullable=True)
    voice_prompt = Column(String, nullable=True)
    voice_path = Column(String, nullable=True) # Oryginalny plik do klonowania
    avatar_path = Column(String, nullable=True)
    
    # --- NOWE POLA ---
    language = Column(String, nullable=True)
    preview_path = Column(String, nullable=True) # Ścieżka do preview.wav
    provider_options = Column(JSON, default={})  # Tu wrzucimy atrybuty Omnivoice, Timbre itd.
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
