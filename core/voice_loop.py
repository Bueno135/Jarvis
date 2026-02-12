import sys
import time
import json
import numpy as np
from core.logger import setup_logger
from threading import Event
from core.kernel import Kernel, SystemState
from core.audio_manager import AudioInputManager
from core.stt import WhisperSTT
from core.input_listener import InputListener

class VoiceLoop:
    """
    Loop principal de interação por voz (Whisper Buffer).
    Conecta: Entrada de Áudio -> Buffer (VAD) -> Whisper STT -> Kernel.
    """
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.logger = setup_logger("Jarvis.VoiceLoop", kernel.config)
        self.config = kernel.config
        
        # Componentes
        self.audio_manager = AudioInputManager(self.config)
        self.stt_service = WhisperSTT(config=self.config) # Whisper
        self.input_listener = InputListener(config=self.config, on_activate=self.on_hotkey_activate)
        
        self.is_running = False
        self.active_listening = False
        self.listening_event = Event()

    def on_hotkey_activate(self):
        self.logger.info(">>> ATIVADO via Hotkey <<<")
        
        # Stop TTS if speaking
        if self.kernel.tts:
             self.kernel.tts.stop()
             
        self.active_listening = True
        self.listening_event.set()

    def start(self):
        self.input_listener.start()
        
        # Model loading happens in STT init
        if not self.stt_service.pipe:
            self.logger.error("Serviço Whisper STT não está pronto (pipe=None).")
            # Continue anyway? Or abort? 
            # Abort to avoid crash
            # return 

        self.logger.info("Sistema pronto (Whisper). Pressione Ctrl+Alt+J.")
        self.is_running = True
        
        try:
            stream = self.audio_manager.start_stream()
            
            # Buffer Configuration
            BUFFER_DURATION = 5.0 # Max seconds per phrase
            SAMPLE_RATE = 16000
            CHANNELS = 1
            # int16 takes 2 bytes per sample.
            # We will store raw bytes in a list and join them.
            
            audio_buffer = []
            is_capturing = False
            silence_start = 0
            has_speech_started = False
            
            # Track trigger type
            self.is_manual_trigger = False

            # VAD Parameters
            SILENCE_TIMEOUT_SPEECH = 1.0    # Stop after 1.0s silence if speech was detected
            SILENCE_TIMEOUT_NO_SPEECH = 5.0 # Stop after 5.0s if no speech detected
            ENERGY_THRESHOLD = 300          # Lowered threshold for better sensitivity
            
            self.logger.info("Aguardando comando...")
            
            for audio_chunk in stream:
                if not self.is_running:
                    break
                
                # Check Hotkey
                # Logic: Always listen if VAD triggers (Energy > Threshold)
                # But only process as command if:
                # 1. Hotkey was pressed (is_capturing=True force)
                # 2. Wake Word is detected in transcription
                
                # Check Hotkey (Manual Activation)
                if self.listening_event.is_set():
                    self.listening_event.clear()
                    is_capturing = True
                    self.is_manual_trigger = True # MARK AS MANUAL
                    audio_buffer = []
                    silence_start = time.time() 
                    has_speech_started = False
                    self.kernel.set_state(SystemState.LISTENING)
                    self.logger.info("Capturando áudio (Hotkey)...")

                # Check Energy (VAD -> Passive Listening)
                # Only if not already capturing manually
                if not is_capturing:
                     chunk_np = np.frombuffer(audio_chunk, dtype=np.int16)
                     if len(chunk_np) > 0:
                        energy = np.sqrt(np.mean(chunk_np.astype(float)**2))
                        if energy > ENERGY_THRESHOLD:
                            # Start passive capture
                            is_capturing = True
                            self.is_manual_trigger = False # MARK AS PASSIVE
                            audio_buffer = []
                            silence_start = time.time()
                            has_speech_started = True # Assume speech started if energy high
                            self.logger.debug("Voz detectada (Passive VAD).")

                if is_capturing:
                    # Append chunk
                    audio_buffer.append(audio_chunk)
                    
                    # Calculate Energy (RMS) to detect silence
                    chunk_np = np.frombuffer(audio_chunk, dtype=np.int16)
                    # Handle potential empty chunk
                    if len(chunk_np) == 0:
                        continue
                        
                    energy = np.sqrt(np.mean(chunk_np.astype(float)**2))
                    
                    if energy > ENERGY_THRESHOLD:
                        silence_start = time.time() # Reset silence timer
                        if not has_speech_started:
                            has_speech_started = True
                            self.logger.debug("Voz detectada via energia.")
                    
                    # Conditions to stop capturing:
                    current_time = time.time()
                    silence_duration = current_time - silence_start
                    
                    # 1. Silence timeout
                    if has_speech_started:
                        if silence_duration > SILENCE_TIMEOUT_SPEECH:
                            self.logger.info(f"Fim de fala detectado ({silence_duration:.1f}s silêncio).")
                            is_capturing = False
                            self.process_buffer(b''.join(audio_buffer), manual_trigger=self.is_manual_trigger)
                            audio_buffer = []
                    else:
                        if silence_duration > SILENCE_TIMEOUT_NO_SPEECH:
                            self.logger.info("Timeout: Nenhuma fala detectada.")
                            is_capturing = False
                            self.process_buffer(b''.join(audio_buffer), manual_trigger=self.is_manual_trigger)
                            audio_buffer = []
                    
                    # 2. Max Buffer Size (Safety)
                    total_bytes = sum(len(c) for c in audio_buffer)
                    if total_bytes > (16000 * 2 * 15): 
                         self.logger.info("Buffer cheio (15s). Processando...")
                         is_capturing = False
                         self.process_buffer(b''.join(audio_buffer), manual_trigger=self.is_manual_trigger)
                         audio_buffer = []

        except KeyboardInterrupt:
             pass
        finally:
             self.is_running = False
             self.input_listener.stop()
             self.audio_manager.stop_stream()
             self.audio_manager.terminate()

    def process_buffer(self, audio_data: bytes, manual_trigger: bool = False):
        if not audio_data:
            return

        self.kernel.set_state(SystemState.PROCESSING)
        self.logger.info(f"Transcrevendo {len(audio_data)} bytes...")
        
        # Transcribe (Blocking or Thread? User said "Use background worker thread")
        # For simplicity in this single-threaded loop, we block briefly. 
        # But user explicitly said "Avoid blocking UI thread" and "Use background worker".
        # Since this loop IS the main voice thread (separate from GUI tray), it's okay to block THIS thread.
        # But if we had a GUI on this thread, we'd need a Worker.
        # Given "Jarvis" structure: voice_loop.start() is called in a thread in main.py?
        # Let's check main.py. voice_loop.start() blocks. main.py starts it in a thread.
        # So blocking here is fine for the voice loop, but it stops listening while transcribing.
        # That's acceptable for "Push-to-Talk" flow.
        
        text = self.stt_service.transcribe(audio_data)
        
        if text:
            # Check for wake word if not manually activated?
            # Actually, we don't know here if it was manual or passive.
            # But we can check if text starts with "Jarvis".
            
            # Wake Word Logic
            raw_wake_word = self.config.get("app", {}).get("wake_word", "jarvis")
            
            # Helper to aggressive normalize (remove spaces, accents, punct)
            import unicodedata
            import string

            def to_id(s):
                if not s: return ""
                # Decode if bytes (unlikely but safety)
                if isinstance(s, bytes):
                    s = s.decode('utf-8', errors='ignore')
                
                # Normalize unicode
                s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('utf-8')
                s = s.lower()
                # Remove punctuation AND SPACES
                s = s.translate(str.maketrans('', '', string.punctuation + " \t\n\r"))
                return s

            wake_id = to_id(raw_wake_word)      # e.g. "sabadofeira"
            text_id = to_id(text)               # e.g. "sabadofeiraquemcriouvoce"

            self.logger.debug(f"Wake check: '{wake_id}' inside '{text_id}'? (Raw Text: {text})")

            # Permissive Variations (Aggressively Normalized)
            # "Sábado Feira" -> "sabadofeira"
            # "Saba do Feira" -> "sabadofeira"
            # "Cabado" -> "cabado"
            possible_triggers = [wake_id]
            
            # Add specific phonetic hacks for "sabado"
            if "sabado" in wake_id:
                possible_triggers.extend(["sabado", "cabado", "saba", "salvador"]) # "salvador" sometimes happens for sabado

            is_wake = False
            for trigger in possible_triggers:
                if trigger and trigger in text_id:
                     is_wake = True
                     self.logger.info(f"Wake Word Detected: detected '{trigger}' in input.")
                     break
            
            if is_wake:
                # Remove the wake word from the start of the text for the command
                # Since we stripped spaces, we can't easily map back index.
                # Heuristic: Remove the first few words if they look like the wake word.
                # Or just pass the whole text. The dispatcher/AI handles extra words well.
                # But "Sábado Feira, que horas são" -> "que horas são" is cleaner.
                
                command_text = text
                
                # Try to strip first 2 words if matches
                words = text.split()
                if len(words) >= 1:
                    # Check first 1-3 words combined
                    check_len = min(len(words), 4)
                    for i in range(check_len, 0, -1):
                        segment = "".join(words[:i])
                        if to_id(segment) in possible_triggers:
                             command_text = " ".join(words[i:]).strip()
                             # Remove leading commma/dots
                             command_text = command_text.lstrip(",.-!?: ")
                             break
                
                if not command_text:
                     self.kernel.speak("Sim?")
                     return

                self.logger.info(f"Comando Processado: {command_text}")
                self.kernel.dispatch(command_text)
            else:
                 if manual_trigger:
                     self.logger.info(f"Comando Manual: {text}")
                     self.kernel.dispatch(text)
                 else:
                     self.logger.info(f"Ignorado (sem wake word): {text}")
                     pass

        else:
            self.logger.warning("Falha na transcrição ou vazio.")
            

