"""
Enhanced audio manager for Jarvis.
Handles model downloading, device management, and fallbacks.
"""
import os
import urllib.request
import zipfile
import logging
from typing import Optional
from pathlib import Path
from core.exceptions import AudioError, STTError, handle_exception
from core.logger import setup_logger

class EnhancedAudioManager:
    """Enhanced audio manager with model management and fallbacks."""
    
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger("Jarvis.EnhancedAudio", config)
        self.stt_provider = config.get("stt", {}).get("provider", "whisper")
        self.model_path = "model"
        
    def ensure_stt_model(self):
        """Ensure STT model is available with download fallback."""
        if self.stt_provider == "vosk":
            self._ensure_vosk_model()
        elif self.stt_provider == "whisper":
            self._ensure_whisper_model()
        else:
            raise AudioError(f"Unsupported STT provider: {self.stt_provider}", provider=self.stt_provider)
            
    def _ensure_vosk_model(self):
        """Download Vosk model if not present."""
        model_dir = Path(self.model_path)
        if model_dir.exists():
            self.logger.info("Vosk model directory exists")
            return
            
        self.logger.info("Downloading Vosk model...")
        self._download_vosk_model(model_dir)
        
    def _download_vosk_model(self, model_dir: Path):
        """Download Vosk model with error handling."""
        try:
            # URL para modelo pequeno em português
            model_url = "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"
            zip_path = "vosk-model.zip"
            
            self.logger.info(f"Downloading model from {model_url}")
            urllib.request.urlretrieve(model_url, zip_path)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.model_path)
                
            os.remove(zip_path)
            self.logger.info("Vosk model downloaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to download Vosk model: {e}")
            raise AudioError(f"Model download failed: {e}", provider="vosk")
            
    def _ensure_whisper_model(self):
        """Ensure Whisper model is available."""
        try:
            import whisper
            model_name = self.config.get("stt", {}).get("model", "tiny")
            
            self.logger.info(f"Loading Whisper model: {model_name}")
            # Whisper will download model automatically if not present
            model = whisper.load_model(model_name)
            self.logger.info("Whisper model ready")
            return model
            
        except ImportError:
            raise STTError("Whisper not installed", provider="whisper")
        except Exception as e:
            raise STTError(f"Failed to load Whisper model: {e}", provider="whisper")
            
    def get_audio_device_info(self):
        """Get information about available audio devices."""
        try:
            import sounddevice as sd
            
            devices = sd.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            
            self.logger.info(f"Found {len(input_devices)} input devices")
            for i, device in enumerate(input_devices):
                self.logger.info(f"  {i}: {device['name']}")
                
            return {
                "total_devices": len(devices),
                "input_devices": len(input_devices),
                "default_input": sd.default.device[0]
            }
            
        except ImportError:
            raise AudioError("sounddevice not available")
        except Exception as e:
            raise AudioError(f"Failed to query audio devices: {e}")
            
    def test_audio_input(self, duration=2):
        """Test audio input functionality."""
        try:
            import sounddevice as sd
            import numpy as np
            
            self.logger.info(f"Testing audio input for {duration} seconds...")
            
            # Record audio
            sample_rate = self.config.get("stt", {}).get("sample_rate", 16000)
            recording = sd.rec(int(duration * sample_rate), 
                             samplerate=sample_rate, 
                             channels=1, dtype='int16')
            sd.wait()
            
            # Check if we got audio
            audio_level = np.sqrt(np.mean(recording.astype(float)**2))
            self.logger.info(f"Audio level: {audio_level:.2f}")
            
            if audio_level < 0.01:
                self.logger.warning("Very low audio level - check microphone")
                
            return {
                "success": True,
                "duration": duration,
                "sample_rate": sample_rate,
                "audio_level": audio_level,
                "samples": len(recording)
            }
            
        except Exception as e:
            raise AudioError(f"Audio test failed: {e}")
            
    def get_optimal_settings(self):
        """Get optimal audio settings based on hardware."""
        device_info = self.get_audio_device_info()
        
        # Default settings
        settings = {
            "sample_rate": 16000,
            "channels": 1,
            "chunk_size": 1024,
            "format": "int16"
        }
        
        # Optimize based on available devices
        if device_info["input_devices"] > 0:
            # Could add more sophisticated optimization here
            pass
            
        return settings
