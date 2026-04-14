import requests
import os
from src.base_provider import BaseTTSProvider
from src.schemas import TTSRequest, TTSResult


class XTTSNetworkProvider(BaseTTSProvider):
    
    @property
    def provider_name(self) -> str:
        return "XTTS Network"
    
    def setup(self):
        self.worker_url = "http://127.0.0.1:8001/generate"
        print(f"[{self.provider_name}] Configured to use XTTS worker at {self.worker_url}")
    
    def generate(self, request: TTSRequest, output_path: str) -> TTSResult:
        
        if not request.voice_path:
            raise ValueError("Voice path is required for XTTS provider.")
        
        language = request.options.get("language", "en")
        print(f"[XTTS Network Provider] Sending generation request for text: '{request.text}' with voice: '{request.voice_path}' and language: '{language}'")
        
        payload = {
            "text": request.text,
            "voice_path": request.voice_path,
            "language": language,
            "output_path": output_path
        }
        
        try:
            response = requests.post(self.worker_url, json=payload)
            response.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            print(f"[XTTS Network Provider] Error occurred while sending generation request: {e}")
            raise RuntimeError(f"Failed to connect to XTTS worker at {self.worker_url}. Is the worker running?") from e
        except Exception as e:
            print(f"[XTTS Network Provider] An error occurred during generation request: {e}")
            raise RuntimeError(f"An error occurred while generating audio: {e}") from e
        
        if not os.path.exists(output_path):
            raise RuntimeError(f"XTTS worker reported success but output file was not found at {output_path}")
        
        return TTSResult(audio_path=output_path,metadata={"provider": self.provider_name, "mode": "xtts_network - microservice"})