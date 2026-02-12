import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.tts.edge_tts_service import EdgeTTSService
import time

# Mock config
config = {
    "tts": {
        "voice": "pt-BR-AntonioNeural",
        "rate": "+0%"
    },
    "logging": {
        "level": "INFO",
        "file": "logs/test_tts.log"
    }
}

print("Initializing TTS Service...")
tts = EdgeTTSService(config)

print("Speaking: 'Olá, este é um teste de voz do Jarvis.'")
tts.speak("Olá, este é um teste de voz do Jarvis.")

print("Speaking: 'Hello World from Edge TTS.'")
tts.speak("Hello World from Edge TTS.")

print("Done.")
