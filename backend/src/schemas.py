from pydantic import BaseModel, Field
from typing import Optional

class TTSRequest(BaseModel):

    text: str = Field(..., description="The text to be converted to speech")
    provider: Optional[str] = Field(default=None, description="The TTS provider to use for synthesis") 
    
    voice_path: Optional[str] = Field(default=None, description="Path to the voice file to be used for synthesis")
    voice_id: Optional[int] = Field(default=None, description="ID of the character voice to use for synthesis")
    voice_prompt: Optional[str] = Field(default=None, description="Optional prompt to guide the voice synthesis")

    device: str = Field(default="cuda", description="Device to use for synthesis (e.g., 'cuda' or 'cpu')")
    options: dict = Field(default_factory=dict, description="Additional options for TTS processing")

class TTSResult(BaseModel):
    audio_path: str = Field(..., description="Path to the generated audio file")
    metadata: dict = Field(default_factory=dict, description="Additional metadata about the TTS result")