import requests
import os
from src.schemas import TTSRequest, TTSResult
from src.base_provider import BaseTTSProvider


class OmniVoiceNetworkProvider(BaseTTSProvider):
    @property
    def provider_name(self) -> str:
        return "omnivoice_network"
    
    def setup(self):
        self.worker_url = "http://127.0.0.1:8003/generate"
        print(f"[{self.provider_name}] Provider setup complete with worker URL: {self.worker_url}")
        
    def generate(self, request: TTSRequest, output_path: str) -> TTSResult:
        print(f"[{self.provider_name}] Generating audio for text: '{request.text[:30]}...'")

        payload = {
            "text": request.text,
            "output_path": output_path,
            "voice_prompt": request.voice_prompt,
            "voice_path": request.voice_path,
            "ref_text": request.options.get("ref_text"),
            "speed": request.options.get("speed", 1.0)
        }

        try:
            response = requests.post(self.worker_url, json=payload)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"[{self.provider_name}] Error: Could not connect to the worker at {self.worker_url}. Please ensure the worker is running and accessible.")
        except Exception as e:
            raise RuntimeError(f"[{self.provider_name}] Error: An error occurred while making the request to the worker: {str(e)}") from e

        return TTSResult(audio_path=output_path, metadata={"provider": self.provider_name, "mode": "network"})