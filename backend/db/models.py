from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import relationship
from db.database import Base

class Character(Base):
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    voice_path = Column(String, nullable=False)
    description = Column(Text)
    avatar_path = Column(String)
    voice_prompt = Column(String)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
