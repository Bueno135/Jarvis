import torch
from transformers import pipeline
from core.interfaces import SpeechToText
from core.logger import setup_logger
import numpy as np
import time

class WhisperSTT(SpeechToText):
    """
    Speech-to-Text conversion using OpenAI Whisper (via Transformers).
    """
    def __init__(self, config=None):
        self.logger = setup_logger("Jarvis.STT.Whisper", config)
        self.config = config or {}
        self.model_id = self.config.get("stt", {}).get("model", "openai/whisper-tiny")
        self.language = self.config.get("stt", {}).get("language", "pt")
        self.device = "cpu" # Force CPU as requested
        self.pipe = None
        
        self._load_model()

    def _load_model(self):
        try:
            self.logger.info(f"Carregando modelo Whisper ({self.model_id}) no {self.device}...")
            start_time = time.time()
            
            # Initialize pipeline
            # generate_kwargs={"language": "portuguese"} forces language
            self.pipe = pipeline(
                "automatic-speech-recognition",
                model=self.model_id,
                device=self.device,
                generate_kwargs={"language": self.language}
            )
            
            end_time = time.time()
            self.logger.info(f"Modelo Whisper carregado em {end_time - start_time:.2f}s.")
        except Exception as e:
            self.logger.error(f"Falha ao carregar Whisper: {e}")
            self.pipe = None

    def transcribe(self, audio: bytes) -> str:
        """
        Transcribes raw PCM audio bytes to text.
        Assumes 16kHz, mono, int16 (standard from AudioInputManager).
        """
        if not self.pipe:
            self.logger.error("Whisper pipeline not initialized.")
            return ""

        try:
            start_time = time.time()
            
            # Convert bytes (int16) to float32 numpy array normalized to [-1, 1]
            # SoundDevice captures int16 usually.
            audio_np = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe
            # pipeline expects numpy array or path
            result = self.pipe(audio_np)
            text = result.get("text", "").strip()
            
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            if text:
                self.logger.info(f"Transcrição ({duration_ms:.0f}ms): '{text}'")
            
            return text
            
        except Exception as e:
            self.logger.error(f"Erro na transcrição: {e}")
            return ""
