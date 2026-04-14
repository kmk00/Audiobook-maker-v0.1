from typing import Callable, Dict, Type, Optional
from uuid import uuid4
import os

from src.base_provider import BaseTTSProvider
from src.schemas import TTSRequest, TTSResult

# from src.providers.xtts2 import XTTS2Provider
from providers.xtts_network import XTTSNetworkProvider
# from src.providers.qwen_tts import QwenTTSProvider
from providers.qwentts_network import QwenNetworkProvider
from providers.omnivoice_network import OmniVoiceNetworkProvider

class TTSManager:
    def __init__(self, output_dir: str = "audiobooks/audio") -> None:
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self._providers: Dict[str, BaseTTSProvider] = {}
        
        # Declare available providers without instantiating them yet
        self._available_providers: Dict[str, Callable[[Optional[dict]], BaseTTSProvider]] = {
            "coqui_xtts_v2": lambda config: XTTSNetworkProvider(config=config),
            
            "qwen_design": lambda config: QwenNetworkProvider(config={"model_id": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", "provider_name": "qwen_design"}),
            "qwen_custom": lambda config: QwenNetworkProvider(config={"model_id": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice", "provider_name": "qwen_custom"}),            
            "qwen_base": lambda config: QwenNetworkProvider(config={"model_id": "Qwen/Qwen3-TTS-12Hz-1.7B-Base", "provider_name": "qwen_base"}),
            
            "omnivoice": lambda config: OmniVoiceNetworkProvider(config=config),
        }
        
        self.active_provider: Optional[str] = None
        
    def load_provider(self, provider_name: str, config: Optional[dict] = None):
        """Load and initialize a TTS provider by name. This method will instantiate the provider and call its setup method."""
        if provider_name not in self._available_providers:
            raise ValueError(f"Provider '{provider_name}' is not available. Available providers: {list(self._available_providers.keys())}")
        
        if provider_name not in self._providers:
            provider_factory = self._available_providers[provider_name]
            self._providers[provider_name] = provider_factory(config)
            print(f"Provider '{provider_name}' loaded successfully.")
            
        self.active_provider = provider_name
        print(f"Provider '{provider_name}' loaded and set as active provider.")
        
    def generate_audio(self, request: TTSRequest, provider_override: Optional[str] = None) -> TTSResult:
        """Generate audio from text using the active provider or an optional provider override. The generated audio will be saved to the output directory with a unique filename. The method returns a TTSResult containing the path to the generated audio and metadata about the provider used."""
        
        target_provider = provider_override or self.active_provider
        
        if not target_provider or target_provider not in self._providers:
            raise ValueError(f"No active provider set and no valid provider override provided. Please load a provider and/or specify a valid provider override.")
        
        provider = self._providers[target_provider]
        
        output_filename = f"{uuid4().hex}.wav"
        output_path = os.path.join(self.output_dir, output_filename)
        
        print(f"Generating audio using provider '{target_provider}' with output path: {output_path}")
        
        return provider.generate(request, output_path)