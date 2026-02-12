import sys
import time
from threading import Event
from core.kernel import Kernel, SystemState
from core.audio_manager import AudioInputManager
from core.stt_service import STTService
from core.input_listener import InputListener

class VoiceLoop:
    """
    Loop principal de interação por voz.
    Conecta: Entrada de Áudio -> STT (Vosk) -> Kernel (Execução).
    Controlado por Hotkey ou Wake Word.
    """
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.logger = kernel.logger
        self.config = kernel.config
        
        # Inicializar componentes
        self.audio_manager = AudioInputManager(self.config)
        self.stt_service = STTService(model_path="model", config=self.config)
        self.input_listener = InputListener(config=self.config, on_activate=self.activate_listening)
        
        # Evento para controlar o estado de escuta
        self.listening_event = Event()

    def activate_listening(self):
        """
        Ativa o modo de escuta (Callback da Hotkey).
        """
        if not self.listening_event.is_set():
            self.logger.info(">>> ATIVADO via Hotkey <<<")
            self.kernel.set_state(SystemState.LISTENING)
            self.listening_event.set()

    def start(self):
        """
        Inicia o loop principal.
        """
        # Iniciar listener de teclado
        self.input_listener.start()
        
        if not self.stt_service.recognizer:
            self.logger.error("Serviço STT não está pronto. Abortando modo de voz.")
            return

        self.logger.info("Sistema pronto. Pressione Ctrl+Alt+J para falar.")
        
        try:
            while True:
                # Aguarda ativação (Bloqueante eficiente)
                self.listening_event.wait()
                
                # Iniciar Stream de áudio
                # Iniciar Stream de áudio
                self.logger.info("Escutando comando...")
                try:
                    start_time = time.time()
                    last_speech_time = time.time()
                    
                    # Configurações de Timeout
                    MAX_DURATION = 15.0 # Tempo máximo total
                    SILENCE_TIMEOUT = 3.0 # Tempo máximo de silêncio após fala ou início
                    
                    found_command = False
                    
                    # Loop de captura de áudio
                    for audio_chunk in self.audio_manager.start_stream():
                        current_time = time.time()
                        
                        # 1. Timeout Total (Segurança)
                        if current_time - start_time > MAX_DURATION:
                            self.logger.info("Timeout total atingido.")
                            break
                        
                        # Processar STT e verificar atividade
                        text, is_speaking = self.stt_service.process_audio(audio_chunk)
                        
                        if is_speaking:
                            last_speech_time = current_time # Resetar timer de silêncio se estiver falando
                            
                        # 2. Timeout de Silêncio
                        # Se não detectou nada novo nos últimos X segundos, assume que acabou
                        if current_time - last_speech_time > SILENCE_TIMEOUT:
                             self.logger.info("Silêncio detectado (Fim de fala).")
                             break
                        
                        if text:
                            self.logger.info(f"Voz detectada: '{text}'")
                            self.kernel.dispatch(text)
                            found_command = True
                            break # Comando processado, sair do loop de áudio
                    
                finally:
                    # Parar stream e resetar estado
                    self.audio_manager.stop_stream()
                    self.listening_event.clear()
                    self.kernel.set_state(SystemState.IDLE)
                    self.logger.info("Aguardando ativação (Ctrl+Alt+J)...")

        except KeyboardInterrupt:
            self.logger.info("Interrompido pelo usuário.")
        finally:
            self.input_listener.stop()
            self.audio_manager.terminate()
