import sys
import time
import json
import numpy as np
import threading
import queue
from core.logger import setup_logger
from threading import Event
from core.kernel import Kernel, SystemState
from core.audio_manager import AudioInputManager
from core.stt import WhisperSTT
from core.input_listener import InputListener

class VoiceLoop:
    """
    Loop principal de interação por voz (Whisper Buffer).
    Conecta: Entrada de Áudio -> Buffer (VAD) -> Queue -> Whisper STT (Worker) -> Kernel.
    Refatorado para arquitetura Produtor-Consumidor (Non-blocking).
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
        
        # Queue for decoupling capture from processing
        self.processing_queue = queue.Queue()

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

        self.logger.info("Sistema pronto (Whisper). Pressione Ctrl+Alt+J.")
        self.is_running = True
        
        # Start Consumer Thread
        self.consumer_thread = threading.Thread(target=self._consumer_worker, daemon=True)
        self.consumer_thread.start()
        
        try:
            stream = self.audio_manager.start_stream()
            
            # Buffer Configuration
            BUFFER_DURATION = 5.0 # Max seconds per phrase
            SAMPLE_RATE = 16000
            ENERGY_THRESHOLD = 300
            
            audio_buffer = []
            is_capturing = False
            silence_start = 0
            has_speech_started = False
            
            # Track trigger type
            self.is_manual_trigger = False

            # VAD Parameters
            SILENCE_TIMEOUT_SPEECH = 1.0    # Stop after 1.0s silence if speech was detected
            SILENCE_TIMEOUT_NO_SPEECH = 5.0 # Stop after 5.0s if no speech detected
            
            self.logger.info("Aguardando comando...")
            
            for audio_chunk in stream:
                if not self.is_running:
                    break
                
                # Check Hotkey
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
                if not is_capturing:
                     chunk_np = np.frombuffer(audio_chunk, dtype=np.int16)
                     if len(chunk_np) > 0:
                        energy = np.sqrt(np.mean(chunk_np.astype(float)**2))
                        if energy > ENERGY_THRESHOLD:
                            is_capturing = True
                            self.is_manual_trigger = False # MARK AS PASSIVE
                            audio_buffer = []
                            silence_start = time.time()
                            has_speech_started = True 
                            self.logger.debug("Voz detectada (Passive VAD).")

                if is_capturing:
                    audio_buffer.append(audio_chunk)
                    
                    chunk_np = np.frombuffer(audio_chunk, dtype=np.int16)
                    if len(chunk_np) == 0: continue
                        
                    energy = np.sqrt(np.mean(chunk_np.astype(float)**2))
                    
                    if energy > ENERGY_THRESHOLD:
                        silence_start = time.time()
                        if not has_speech_started:
                            has_speech_started = True
                            self.logger.debug("Voz detectada via energia.")
                    
                    current_time = time.time()
                    silence_duration = current_time - silence_start
                    
                    # Check End Conditions
                    should_process = False
                    if has_speech_started:
                        if silence_duration > SILENCE_TIMEOUT_SPEECH:
                            self.logger.info(f"Fim de fala detectado ({silence_duration:.1f}s silêncio).")
                            should_process = True
                    else:
                        if silence_duration > SILENCE_TIMEOUT_NO_SPEECH:
                            self.logger.info("Timeout: Nenhuma fala detectada.")
                            should_process = True
                            
                    # Max Buffer Check
                    total_bytes = sum(len(c) for c in audio_buffer)
                    if total_bytes > (16000 * 2 * 15): 
                         self.logger.info("Buffer cheio (15s). processando...")
                         should_process = True

                    if should_process:
                        is_capturing = False
                        # Enqueue for processing
                        self.processing_queue.put({
                            "audio": b''.join(audio_buffer),
                            "manual": self.is_manual_trigger
                        })
                        audio_buffer = []

        except KeyboardInterrupt:
             pass
        finally:
             self.is_running = False
             self.input_listener.stop()
             self.audio_manager.stop_stream()
             self.audio_manager.terminate()

    def _consumer_worker(self):
        """
        Consumes audio from queue and processes it (Transcribe -> Execute).
        Runs in a separate thread.
        """
        while self.is_running:
            try:
                # Wait for audio (blocking)
                item = self.processing_queue.get(timeout=1.0) 
            except queue.Empty:
                continue
                
            audio_data = item["audio"]
            manual_trigger = item["manual"]
            
            if not audio_data:
                continue

            self.kernel.set_state(SystemState.PROCESSING)
            self.logger.info(f"Processando {len(audio_data)} bytes...")
            
            try:
                # Transcribe
                text = self.stt_service.transcribe(audio_data)
                
                if text:
                    self.process_text_command(text, manual_trigger)
                else:
                    self.logger.warning("Transcrição vazia.")
            except Exception as e:
                self.logger.error(f"Erro no processamento de áudio: {e}")
            
            self.kernel.set_state(SystemState.IDLE)
            self.processing_queue.task_done()

    def process_text_command(self, text: str, manual_trigger: bool):
        """
        Logic to handle transcribed text: Wake Word Check -> Dispatch.
        """
        # Wake Word Logic
        raw_wake_word = self.config.get("app", {}).get("wake_word", "jarvis")
        
        # Helper to aggressive normalize
        import unicodedata
        import string

        def to_id(s):
            if not s: return ""
            if isinstance(s, bytes): s = s.decode('utf-8', errors='ignore')
            s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('utf-8')
            s = s.lower()
            s = s.translate(str.maketrans('', '', string.punctuation + " \t\n\r"))
            return s

        wake_id = to_id(raw_wake_word)
        text_id = to_id(text)

        self.logger.debug(f"Wake check: '{wake_id}' inside '{text_id}'? (Raw: {text})")

        possible_triggers = [wake_id]
        if "sabado" in wake_id:
            possible_triggers.extend(["sabado", "cabado", "saba", "salvador"])

        is_wake = False
        for trigger in possible_triggers:
            if trigger and trigger in text_id:
                    is_wake = True
                    self.logger.info(f"Wake Word Detected: '{trigger}'")
                    break
        
        if is_wake:
            command_text = text
            # Heuristic to remove wake word words
            # Simple approach: pass full text if confident, or strip first few words?
            # Let's keep passing full text for now as it works well with AI
            
            self.logger.info(f"Comando Processado: {command_text}")
            self.kernel.dispatch(command_text)
        else:
                if manual_trigger:
                    self.logger.info(f"Comando Manual: {text}")
                    self.kernel.dispatch(text)
                else:
                    self.logger.info(f"Ignorado (sem wake word): {text}")
