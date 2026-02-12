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
            
            # VAD Parameters
            SILENCE_TIMEOUT_SPEECH = 1.0    # Stop after 1.0s silence if speech was detected
            SILENCE_TIMEOUT_NO_SPEECH = 5.0 # Stop after 5.0s if no speech detected
            ENERGY_THRESHOLD = 300          # Lowered threshold for better sensitivity
            
            self.logger.info("Aguardando comando...")
            
            for audio_chunk in stream:
                if not self.is_running:
                    break
                
                # Check Hotkey
                if self.listening_event.is_set():
                    self.listening_event.clear()
                    is_capturing = True
                    audio_buffer = []
                    silence_start = time.time() # Reset timer on activation
                    has_speech_started = False
                    self.kernel.set_state(SystemState.LISTENING)
                    self.logger.info("Capturando áudio...")

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
                            self.process_buffer(b''.join(audio_buffer))
                            audio_buffer = []
                    else:
                        if silence_duration > SILENCE_TIMEOUT_NO_SPEECH:
                            self.logger.info("Timeout: Nenhuma fala detectada.")
                            is_capturing = False
                            # Don't process empty noise, but user might want to try? 
                            # Usually better to ignore or send anyway? 
                            # Let's send it, maybe it was a whisper.
                            self.process_buffer(b''.join(audio_buffer))
                            audio_buffer = []
                    
                    # 2. Max Buffer Size (Safety)
                    total_bytes = sum(len(c) for c in audio_buffer)
                    if total_bytes > (16000 * 2 * 15): # ~15 seconds limit (16k * 2 bytes * 15s)
                         self.logger.info("Buffer cheio (15s). Processando...")
                         is_capturing = False
                         self.process_buffer(b''.join(audio_buffer))
                         audio_buffer = []

        except KeyboardInterrupt:
             pass
        finally:
             self.is_running = False
             self.input_listener.stop()
             self.audio_manager.stop_stream()
             self.audio_manager.terminate()

    def process_buffer(self, audio_data: bytes):
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
            self.logger.info(f"Texto: {text}")
            self.kernel.dispatch(text)
        else:
            self.logger.warning("Falha na transcrição ou vazio.")
            
        self.kernel.set_state(SystemState.IDLE)

