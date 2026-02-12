from vosk import Model, KaldiRecognizer
import json
import os
from typing import Optional
from core.logger import setup_logger

class STTService:
    """
    Serviço de Speech-to-Text usando Vosk (Offline).
    """
    def __init__(self, model_path="model", config=None):
        self.logger = setup_logger("Jarvis.STT", config)
        self.model_path = model_path
        self.recognizer: Optional[KaldiRecognizer] = None
        self._load_model()

    def _load_model(self):
        if not os.path.exists(self.model_path):
            self.logger.error(f"Modelo Vosk não encontrado em: {self.model_path}")
            self.logger.warning("Por favor baixe um modelo em https://alphacephei.com/vosk/models e extraia na pasta 'model'")
            return

        try:
            self.logger.info(f"Carregando modelo Vosk de: {self.model_path}...")
            model = Model(self.model_path)
            self.recognizer = KaldiRecognizer(model, 16000)
            self.logger.info("Modelo Vosk carregado com sucesso.")
        except Exception as e:
            self.logger.error(f"Falha ao carregar modelo Vosk: {e}")

    def process_audio(self, data: bytes) -> tuple[Optional[str], bool]:
        """
        Processa um chunk de áudio.
        Retorna (texto_final, is_speaking).
        is_speaking é True se o reconhecedor detectar fala (mesmo parcial).
        """
        if not self.recognizer:
            return None, False

        if self.recognizer.AcceptWaveform(data):
            result_json = self.recognizer.Result()
            result = json.loads(result_json)
            text = result.get("text", "")
            return text, False # Finalizou frase
        else:
            # Verifica parciais para saber se usuário está falando
            partial_json = self.recognizer.PartialResult()
            partial = json.loads(partial_json)
            is_speaking = bool(partial.get("partial", ""))
            return None, is_speaking
