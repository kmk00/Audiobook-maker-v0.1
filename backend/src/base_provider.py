from abc import ABC, abstractmethod
from typing import List, Optional
from src.schemas import TTSRequest, TTSResult

class BaseTTSProvider(ABC):
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}  
        self.setup()
        
    def setup(self):
        """Optional setup method for provider-specific initialization."""
        pass
    
    def cleanup(self):
        """Clean up any resources if necessary (e.g., unload models from GPU)."""
        pass
    
    @abstractmethod
    def generate(self,request: TTSRequest, output_path:str) -> TTSResult:
        """Generate speech from text based on the provided request and save to output_path."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the TTS provider."""
        pass