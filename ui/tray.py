import pystray
from PIL import Image, ImageDraw
from core.kernel import Kernel
import threading
import sys
import signal

# Global shutdown event for graceful termination
_shutdown_event = threading.Event()


class SystemTray:
    """
    Ícone de bandeja do sistema para controle do assistente.
    """
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.logger = kernel.logger
        self.icon = None
        self._shutdown_callbacks = []

    def register_shutdown_callback(self, callback):
        """
        Register a callback to be called during graceful shutdown.
        """
        self._shutdown_callbacks.append(callback)

    def create_icon(self):
        """
        Cria a imagem do ícone programaticamente (para não depender de assets externos no MVP).
        """
        width = 64
        height = 64
        color1 = "black"
        color2 = "cyan"
        
        image = Image.new('RGB', (width, height), color1)
        dc = ImageDraw.Draw(image)
        dc.ellipse((10, 10, 54, 54), fill=color2)
        dc.ellipse((20, 20, 44, 44), fill=color1)
        
        return image

    def on_exit(self, icon, item):
        """
        Callback de saída com shutdown graceful.
        """
        self.logger.info("Encerrando via System Tray...")
        self._graceful_shutdown()

    def _graceful_shutdown(self):
        """
        Performs graceful shutdown of all components.
        """
        # Signal shutdown to all threads
        _shutdown_event.set()
        
        # Call registered shutdown callbacks
        for callback in self._shutdown_callbacks:
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in shutdown callback: {e}")
        
        # Stop TTS if available
        if self.kernel.tts:
            try:
                self.kernel.tts.stop()
            except Exception as e:
                self.logger.debug(f"Error stopping TTS: {e}")
        
        # Stop the tray icon
        if self.icon:
            self.icon.stop()
        
        self.logger.info("Shutdown completo.")
        # Use sys.exit for cleaner shutdown (allows finally blocks to run)
        sys.exit(0)

    def run(self):
        """
        Inicia o System Tray (Bloqueante, deve rodar em thread separada ou ser o main thread).
        """
        # Register signal handlers for graceful shutdown
        try:
            signal.signal(signal.SIGINT, lambda s, f: self._graceful_shutdown())
            signal.signal(signal.SIGTERM, lambda s, f: self._graceful_shutdown())
        except (ValueError, OSError):
            # Signal handling may fail in non-main thread
            pass
        
        image = self.create_icon()
        menu = (
            pystray.MenuItem('Jarvis', lambda: None, enabled=False),
            pystray.MenuItem('Sair', self.on_exit)
        )
        
        self.icon = pystray.Icon("Jarvis", image, "Jarvis Assistant", menu)
        self.logger.info("System Tray iniciado.")
        self.icon.run()

    def start_detached(self):
        """
        Roda o ícone em uma thread separada (não recomendado para alguns frameworks UI, mas OK para pystray em alguns casos).
        """
        t = threading.Thread(target=self.run)
        t.daemon = True
        t.start()


def is_shutdown_requested() -> bool:
    """
    Check if shutdown has been requested. Use this in long-running loops.
    """
    return _shutdown_event.is_set()
