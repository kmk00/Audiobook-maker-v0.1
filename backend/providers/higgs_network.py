import requests
import os
from src.schemas import TTSRequest, TTSResult
from src.base_provider import BaseTTSProvider

class HiggsNetworkProvider(BaseTTSProvider):
    @property
    def provider_name(self) -> str:
        return "higgs_tts_3"

    def setup(self):
        self.worker_url = "http://worker-higgs:8000/v1/audio/speech"
        print(f"[{self.provider_name}] Provider setup complete. Pointing to worker URL: {self.worker_url}")

    def _to_container_path(self, local_voice_path: str) -> str:
        normalized = local_voice_path.replace("\\", "/").lstrip("/")
        return f"docs/_static/audio/{normalized}"

    def generate(self, request: TTSRequest, output_path: str) -> TTSResult:
        print(f"[{self.provider_name}] Generating audio for text: '{request.text[:30]}...'")

        payload = {
            "model": "bosonai/higgs-tts-3-4b",
            "input": request.text
        }

        if request.voice_path and os.path.exists(request.voice_path):
            print(f"[{self.provider_name}] Voice cloning mode detected.")
            ref_item = {"audio_path": self._to_container_path(request.voice_path)}

            ref_text = request.options.get("ref_text")
            if ref_text:
                ref_item["text"] = ref_text

            payload["references"] = [ref_item]

        if "temperature" in request.options:
            payload["temperature"] = float(request.options["temperature"])
        if "top_k" in request.options:
            payload["top_k"] = int(request.options["top_k"])

        try:
            response = requests.post(self.worker_url, json=payload, timeout=120)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(response.content)

            print(f"[{self.provider_name}] Audio generated and saved to: {output_path}")

        except requests.exceptions.ConnectionError:
            raise RuntimeError(f"[{self.provider_name}] Error: Nie można połączyć się z Higgs na {self.worker_url}. Upewnij się, że kontener sglang-omni działa.")
        except requests.exceptions.Timeout:
            raise RuntimeError(f"[{self.provider_name}] Error: Timeout — generowanie trwało zbyt długo.")
        except Exception as e:
            raise RuntimeError(f"[{self.provider_name}] Error: Błąd API Higgs: {str(e)}")

        return TTSResult(audio_path=output_path, metadata={"provider": self.provider_name, "mode": "network"})