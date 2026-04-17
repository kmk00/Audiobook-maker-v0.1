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
    voice_path = Column(String, nullable=True) 
    avatar_path = Column(String, nullable=True)
    
    language = Column(String, nullable=True)
    preview_path = Column(String, nullable=True) 
    provider_options = Column(JSON, default={})  
    
    category = Column(String, nullable=True)
    tags = Column(JSON, default=[])
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
