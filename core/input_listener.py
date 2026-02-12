import keyboard
import time
from typing import Callable, Optional
from core.logger import setup_logger

class InputListener:
    """
    Gerencia gatilhos de entrada global (Teclado).
    Permite ativar o assistente via Hotkey.
    """
    def __init__(self, config=None, on_activate: Optional[Callable] = None):
        self.logger = setup_logger("Jarvis.Input", config)
        self.config = config
        self.hotkey = "ctrl+alt+j" # Padrão
        self.on_activate = on_activate
        self.is_running = False

    def start(self):
        """
        Inicia o listener de teclado em background.
        """
        if not self.on_activate:
            self.logger.warning("Nenhuma função de callback definida para o InputListener.")
            return

        try:
            self.logger.info(f"Registrando hotkey global: {self.hotkey}")
            keyboard.add_hotkey(self.hotkey, self._trigger_activation)
            self.is_running = True
        except Exception as e:
            self.logger.error(f"Falha ao registrar hotkey: {e}")

    def _trigger_activation(self):
        """
        Callback interno acionado pela hotkey.
        """
        self.logger.info("Hotkey detectada! Ativando...")
        if self.on_activate:
            self.on_activate()

    def stop(self):
        """
        Remove os hooks de teclado.
        """
        try:
            keyboard.remove_hotkey(self.hotkey)
            self.is_running = False
        except:
            pass
