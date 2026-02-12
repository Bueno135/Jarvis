import tkinter as tk
import threading
import time
from core.kernel import Kernel, SystemState

class OverlayUI:
    """
    Interface flutuante minimalista para feedback visual.
    """
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.root = None
        self.label = None
        self.is_running = False

    def run(self):
        """
        Inicia a UI em uma thread separada (Tkinter mainloop).
        """
        self.is_running = True
        self.thread = threading.Thread(target=self._start_gui, daemon=True)
        self.thread.start()
        
        # Inscrever-se em eventos do Kernel para atualizar a UI
        self.kernel.subscribe("state_changed", self.on_state_changed)

    def _start_gui(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True) # Remove bordas da janela
        self.root.attributes("-topmost", True) # Sempre no topo
        self.root.geometry("200x50+10+10") # Tamanho e posição (Topo Esquerdo)
        self.root.configure(bg='black')
        
        # Opacidade (Alpha)
        self.root.attributes("-alpha", 0.8)

        self.label = tk.Label(
            self.root, 
            text="Jarvis: Idle", 
            fg="white", 
            bg="black", 
            font=("Arial", 12)
        )
        self.label.pack(expand=True, fill='both')

        self.root.mainloop()

    def on_state_changed(self, payload):
        """
        Atualiza o texto da UI baseado no estado.
        """
        if self.label:
            new_state = payload.get("new", "UNKNOWN")
            
            color_map = {
                "IDLE": "gray",
                "LISTENING": "cyan",
                "PROCESSING": "yellow",
                "EXECUTING": "green",
                "ERROR": "red"
            }
            
            bg_color = color_map.get(new_state, "black")
            
            # Atualização deve ser thread-safe em Tkinter? 
            # Geralmente sim, mas idealmente usar after() se falhar.
            try:
                self.label.config(text=f"Jarvis: {new_state}", fg=bg_color)
            except:
                pass

    def stop(self):
        if self.root:
            self.root.quit()
        self.is_running = False
