import tkinter as tk
import threading
import logging
from core.kernel import Kernel, SystemState

logger = logging.getLogger("Jarvis.UI.Overlay")


class OverlayUI:
    """
    Interface flutuante minimalista para feedback visual.
    """
    STATE_COLORS = {
        "IDLE": "gray",
        "LISTENING": "cyan",
        "PROCESSING": "yellow",
        "EXECUTING": "green",
        "ERROR": "red"
    }

    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.root = None
        self.label = None
        self.is_running = False
        self._gui_ready = threading.Event()

    def run(self):
        """
        Inicia a UI em uma thread separada (Tkinter mainloop).
        """
        self.is_running = True
        self.thread = threading.Thread(target=self._start_gui, daemon=True)
        self.thread.start()
        
        # Wait for GUI to be ready before subscribing to events
        self._gui_ready.wait(timeout=5.0)
        
        # Inscrever-se em eventos do Kernel para atualizar a UI
        self.kernel.subscribe("state_changed", self.on_state_changed)

    def _start_gui(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # Remove bordas da janela
        self.root.attributes("-topmost", True)  # Sempre no topo
        self.root.geometry("200x50+10+10")  # Tamanho e posição (Topo Esquerdo)
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
        
        # Signal that GUI is ready
        self._gui_ready.set()

        self.root.mainloop()

    def on_state_changed(self, payload):
        """
        Atualiza o texto da UI baseado no estado.
        Thread-safe using root.after() to schedule on main thread.
        """
        if self.root and self.label:
            new_state = payload.get("new", "UNKNOWN")
            # Schedule update on Tkinter's main thread
            try:
                self.root.after(0, lambda: self._update_label(new_state))
            except tk.TclError as e:
                logger.debug(f"Could not schedule UI update: {e}")
            except RuntimeError as e:
                logger.debug(f"Runtime error during UI update: {e}")

    def _update_label(self, state: str):
        """
        Actually updates the label. Must be called from Tkinter main thread.
        """
        if self.label and self.is_running:
            color = self.STATE_COLORS.get(state, "white")
            try:
                self.label.config(text=f"Jarvis: {state}", fg=color)
            except tk.TclError as e:
                logger.debug(f"Could not update label: {e}")

    def stop(self):
        self.is_running = False
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except tk.TclError:
                pass  # Already destroyed
