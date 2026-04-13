import os
import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel

from src.schemas import TTSRequest, TTSResult
from src.base_provider import BaseTTSProvider

class QwenTTSProvider(BaseTTSProvider):
    @property
    def provider_name(self) -> str:
        # Pamiętaj, żeby tu też odwołać się do odpowiedniego klucza z konfiguracji!
        return self.config.get("provider_name", "qwen_tts")
    
    def setup(self):
        self.model_id = self.config.get("model_id")
        
        if not self.model_id:
            raise ValueError("Model ID must be specified in the provider configuration.")

        print(f"[{self.provider_name}] Checking for GPU availability...")
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"

        print(f"[{self.provider_name}] Loading model '{self.model_id}' on device '{self.device}'...")
        

        self.model = Qwen3TTSModel.from_pretrained(
            self.model_id,
            device_map=self.device,
            dtype=torch.bfloat16,
            # attn_implementation="flash_attention_2",
        )
        print(f"[{self.provider_name}] Model loaded successfully!")
        
    def generate(self,request:TTSRequest,output_path:str) -> TTSResult:
        language = request.options.get("language", "Auto")
        
        print(f"[{self.provider_name}] Generating speech for text: {request.text[:30]}...")
        
        current_model = str(self.model_id)

        if "VoiceDesign" in current_model:
            wavs, sr = self.model.generate_voice_design(
                text=request.text,
                language=language,
                instruct=request.voice_prompt or ""
            )
            
        elif "CustomVoice" in current_model:
            speaker = request.options.get("speaker", "Vivian") 
            wavs, sr = self.model.generate_custom_voice(
                text=request.text,
                language=language,
                speaker=speaker,
                instruct=request.voice_prompt or ""
            )
            
        elif "Base" in current_model:
            
            if not request.voice_path or not os.path.exists(request.voice_path):
                raise ValueError(f"[{self.provider_name}] ERROR: Voice cloning requires a valid path in 'voice_path'.")
            
            ref_text = request.options.get("ref_text")
            if not ref_text:
                raise ValueError(f"[{self.provider_name}] ERROR: Base model requires 'ref_text' in options (transcription of the reference file).")
            
            wavs, sr = self.model.generate_voice_clone(
                text=request.text,
                language=language,
                ref_audio=request.voice_path,
                ref_text=ref_text
            )
        else:
            raise ValueError(f"[{self.provider_name}] ERROR: Unknown variant of Qwen model: {self.model_id}")

        sf.write(output_path, wavs[0], sr)
        print(f"[{self.provider_name}] Generated file saved to: {output_path}")

        return TTSResult(
            audio_path=output_path,
            metadata={"provider": self.provider_name, "model": self.model_id}
        )