import os
import torch



from src.base_provider import BaseTTSProvider
from src.schemas import TTSRequest, TTSResult


class XTTS2Provider(BaseTTSProvider):
    @property
    def provider_name(self) -> str:
        return "coqui_xtts_v2"

    def setup(self):
        from TTS.api import TTS
        import torchaudio
        import soundfile as sf
        
        # --- PyTorch 2.6 compatibility patch ---
        _original_torch_load = torch.load
        def _patched_torch_load(*args, **kwargs):
            kwargs.setdefault("weights_only", False)
            return _original_torch_load(*args, **kwargs)
        torch.load = _patched_torch_load

        # --- Patch torchaudio.load to use soundfile directly ---
        def _patched_torchaudio_load(filepath, *args, **kwargs):
            data, sample_rate = sf.read(filepath, dtype="float32", always_2d=True)
            return torch.tensor(data.T), sample_rate

        torchaudio.load = _patched_torchaudio_load
        # -------------------------------------------------------


        
        print(f"[{self.provider_name}] Checking for GPU availability...")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        print(f"[{self.provider_name}] Loading model on device: {self.device}. This might take a moment...")
        
        self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
        
        print(f"[{self.provider_name}] Model loaded successfully!")

    def generate(self, request: TTSRequest, output_path: str) -> TTSResult:
        """
        Generate speech from text using Coqui TTS XTTS v2 model. This model requires a reference voice sample for cloning, which should be provided in the 'voice_path' field of the TTSRequest. The generated audio will be saved to the specified output path. The method returns a TTSResult containing the path to the generated audio and metadata about the provider used.
        
        @param request [TTSRequest]: Object containing the text to be synthesized and optional parameters such as voice_path and options.
        
        @param output_path [str]: The file path where the generated audio will be saved.
        """

        if not request.voice_path:
            raise ValueError(
                f"[{self.provider_name}] ERROR: XTTS v2 model requires a reference voice sample for cloning. Please provide a valid 'voice_path' in the TTSRequest."
                "Enter a valid path to a voice sample file (e.g., 'path/to/voice_sample.wav') in the 'voice_path' field of the TTSRequest."
            )
            
        if not os.path.exists(request.voice_path):
            raise FileNotFoundError(
                f"[{self.provider_name}] ERROR: File not found at path: {request.voice_path}"
            )

        language = request.options.get("language", "pl")
        
        print(f"[{self.provider_name}] Generating speech for text: '{request.text}' using voice sample: '{request.voice_path}' with language: '{language}'")
        
        self.model.tts_to_file(
            text=request.text,
            speaker_wav=request.voice_path,
            language=language,
            file_path=output_path
        )
        
        print(f"[{self.provider_name}] Generated audio has been saved to: {output_path}")

        return TTSResult(
            audio_path=output_path,
            metadata={"provider": self.provider_name},
        )
    
    