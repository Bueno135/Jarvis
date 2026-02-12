import os
import asyncio
import edge_tts
import pygame
import tempfile
import threading
from core.interfaces import TextToSpeech
from core.logger import setup_logger

class EdgeTTSService(TextToSpeech):
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger("Jarvis.TTS.Edge", config)
        self.voice = config.get("tts", {}).get("voice", "pt-BR-AntonioNeural")
        self.rate = config.get("tts", {}).get("rate", "+0%")
        
        # Init Pygame Mixer
        try:
            pygame.mixer.init()
        except Exception as e:
            self.logger.error(f"Failed to init pygame mixer: {e}")

    def speak(self, text: str) -> None:
        """
        Synthesizes speech from text and plays it.
        """
        if not text:
            return

        try:
            # Create a dedicated thread for the asyncio loop to avoid blocking logic
            # or conflict with main thread loop if any.
            # Ideally we should use a shared loop or simply run.
            # Since this is a simple fire-and-forget for now:
            threading.Thread(target=self._run_async, args=(text,), daemon=True).start()
        except Exception as e:
            self.logger.error(f"TTS Error: {e}")

    def is_busy(self) -> bool:
        """
        Returns True if audio is playing.
        """
        try:
            return pygame.mixer.music.get_busy()
        except:
            return False

    def stop(self) -> None:
        """
        Stops current playback.
        """
        try:
            if self.is_busy():
                pygame.mixer.music.stop()
        except Exception as e:
            self.logger.error(f"Error stopping TTS: {e}")

    def _run_async(self, text: str):
        try:
            asyncio.run(self._generate_and_play(text))
        except Exception as e:
             self.logger.error(f"TTS Thread Error: {e}")

    async def _generate_and_play(self, text: str):
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_path = tmp_file.name

        try:
            await communicate.save(tmp_path)
            
            # Play
            self.logger.info(f"Speaking: {text}")
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            # Unload to release file lock
            pygame.mixer.music.unload()
            
        except Exception as e:
            self.logger.error(f"Playback Error: {e}")
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass
