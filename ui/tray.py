import pystray
from PIL import Image, ImageDraw
from core.kernel import Kernel
import threading
import os
import sys

class SystemTray:
    """
    Ícone de bandeja do sistema para controle do assistente.
    """
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.logger = kernel.logger
        self.icon = None

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
        Callback de saída.
        """
        self.logger.info("Encerrando via System Tray...")
        icon.stop()
        os._exit(0) # Forçar saída de todas as threads

    def run(self):
        """
        Inicia o System Tray (Bloqueante, deve rodar em thread separada ou ser o main thread).
        """
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
