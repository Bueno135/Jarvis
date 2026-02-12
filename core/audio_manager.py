import sounddevice as sd
import queue
import sys
from typing import Generator
from core.logger import setup_logger

class AudioInputManager:
    """
    Gerencia a captura de áudio do microfone usando SoundDevice.
    Substitui o PyAudio para melhor compatibilidade com Windows.
    """
    def __init__(self, config=None):
        self.logger = setup_logger("Jarvis.Audio", config)
        self.samplerate = 16000 # Vosk requer 16khz
        self.channels = 1
        self.dtype = 'int16'
        self.blocksize = 4096
        self.q = queue.Queue()
        self.is_listening = False
        self.stream = None

    def _audio_callback(self, indata, frames, time, status):
        """
        Callback chamado pelo sounddevice a cada bloco de áudio.
        """
        if status:
            self.logger.warning(f"Status de áudio: {status}")
        self.q.put(bytes(indata))

    def start_stream(self) -> Generator[bytes, None, None]:
        """
        Inicia a captura de áudio e gera chunks de bytes.
        """
        try:
            self.stream = sd.RawInputStream(
                samplerate=self.samplerate,
                blocksize=self.blocksize,
                dtype=self.dtype,
                channels=self.channels,
                callback=self._audio_callback
            )
            
            self.is_listening = True
            self.logger.info(f"Stream de áudio (SoundDevice) iniciado a {self.samplerate}Hz. Escutando...")
            
            with self.stream:
                while self.is_listening:
                    try:
                        data = self.q.get(timeout=1.0) # Timeout para permitir verificar flag is_listening
                        yield data
                    except queue.Empty:
                        if not self.stream.active:
                            break
                        continue
                
        except Exception as e:
            self.logger.error(f"Erro no stream de áudio: {e}")
            self.stop_stream()

    def stop_stream(self):
        """
        Sinaliza para parar o loop de leitura.
        """
        self.is_listening = False
        self.logger.info("Parando stream de áudio...")

    def terminate(self):
        """
        Libera recursos (SoundDevice gerencia isso com contexto, mas mantemos interface).
        """
        self.stop_stream()

