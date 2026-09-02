import requests
from src.schemas import TTSRequest, TTSResult
from src.base_provider import BaseTTSProvider


class BreezeTTSNetworkProvider(BaseTTSProvider):
    @property
    def provider_name(self) -> str:
        return "breeze_network"

    def setup(self):
        self.worker_url = "http://worker-breeze:8003/generate"
        print(f"[{self.provider_name}] Provider setup complete with worker URL: {self.worker_url}")

    def generate(self, request: TTSRequest, output_path: str) -> TTSResult:
        print(f"[{self.provider_name}] Generating audio for text: '{request.text[:30]}...'")

        # Per-line direction (from `<<...>>` markup) takes precedence over the
        # character's default voice_prompt / instruction.
        instruction = request.options.get("direction") or request.voice_prompt

        payload = {
            "text": request.text,
            "output_path": output_path,
            "ref_audio": request.voice_path,
            "ref_text": request.options.get("ref_text"),
            "instruction": instruction,
            "cfg_scale": request.options.get("cfg_scale", 4.0),
            "seed": request.options.get("seed", 42),
        }

        try:
            response = requests.post(self.worker_url, json=payload)
            response.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"[{self.provider_name}] Error: Could not connect to the worker at {self.worker_url}. Please ensure the worker is running and accessible.")
        except Exception as e:
            raise RuntimeError(f"[{self.provider_name}] Error: An error occurred while making the request to the worker: {str(e)}") from e

        return TTSResult(audio_path=output_path, metadata={"provider": self.provider_name, "mode": "network"})
