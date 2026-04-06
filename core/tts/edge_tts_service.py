import os
import asyncio
import edge_tts
import tempfile
import threading
import subprocess
import platform
from core.interfaces import TextToSpeech
from core.logger import setup_logger

class EdgeTTSService(TextToSpeech):
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger("Jarvis.TTS.Edge", config)
        self.voice = config.get("tts", {}).get("voice", "pt-BR-AntonioNeural")
        self.rate = config.get("tts", {}).get("rate", "+0%")
        self.is_playing = False
        
        # Initialize audio system
        self._init_audio_system()

    def _init_audio_system(self):
        """Initialize audio playback system based on platform."""
        try:
            if platform.system() == "Windows":
                # Use Windows built-in media player
                self.logger.info("Using Windows audio playback")
            elif platform.system() == "Darwin":  # macOS
                # Use afplay on macOS
                self.logger.info("Using macOS audio playback")
            else:
                # Use aplay on Linux
                self.logger.info("Using Linux audio playback")
        except Exception as e:
            self.logger.error(f"Failed to init audio system: {e}")

    def speak(self, text: str) -> None:
        """
        Synthesizes speech from text and plays it.
        """
        if not text:
            return

        try:
            # Create a dedicated thread for the asyncio loop
            threading.Thread(target=self._run_async, args=(text,), daemon=True).start()
        except Exception as e:
            self.logger.error(f"TTS Error: {e}")

    def is_busy(self) -> bool:
        """
        Returns True if audio is playing.
        """
        return self.is_playing

    def stop(self) -> None:
        """
        Stops current playback.
        """
        try:
            self.is_playing = False
            self.logger.info("TTS playback stopped")
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
            
            # Play using system audio player
            self.logger.info(f"Speaking: {text}")
            self.is_playing = True
            self._play_audio_file(tmp_path)
                
        except Exception as e:
            self.logger.error(f"Playback Error: {e}")
        finally:
            self.is_playing = False
            # Clean up
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError as e:
                    self.logger.debug(f"Could not delete temp file {tmp_path}: {e}")

    def _play_audio_file(self, file_path: str):
        """Play audio file using system's default audio player."""
        try:
            if platform.system() == "Windows":
                # Use Windows Media Player or start command
                subprocess.run(["start", "/min", file_path], shell=True, check=True)
                # Wait a bit for the file to start playing
                import time
                time.sleep(1)
                # Estimate playback time (rough calculation: ~1 second per 10KB)
                file_size = os.path.getsize(file_path)
                estimated_duration = max(file_size / 10240, 2)  # At least 2 seconds
                time.sleep(estimated_duration)
                
            elif platform.system() == "Darwin":  # macOS
                # Use afplay
                subprocess.run(["afplay", file_path], check=True)
                
            else:  # Linux
                # Try different Linux audio players
                players = ["aplay", "mpg123", "mplayer", "vlc"]
                for player in players:
                    try:
                        subprocess.run([player, file_path], check=True, 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                else:
                    self.logger.warning("No suitable audio player found on Linux")
                    
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Audio playback failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in audio playback: {e}")
