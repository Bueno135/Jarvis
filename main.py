import sys
import os
print(f"DEBUG: Executable: {sys.executable}")
print(f"DEBUG: Path: {sys.path}")
print(f"DEBUG: CWD: {os.getcwd()}")
try:
    import google
    print(f"DEBUG: google package: {google.__path__}")
except ImportError:
    print("DEBUG: Could not import 'google' package")

import google.generativeai # Force load first
import argparse
import sys
import yaml
import os
from core.kernel import Kernel, SystemState
from core.interfaces import CommandResult


def load_config(path="config/config.yaml"):
    if not os.path.exists(path):
        print(f"Config file not found at {path}. Using defaults.")
        return {}
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description="Jarvis - Local Voice Assistant")
    parser.add_argument("--text", type=str, help="Run a text command directly and exit")
    args = parser.parse_args()

    # 1. Load Config
    config = load_config()

    # 2. Initialize Kernel
    kernel = Kernel(config)

    # 3. Load Plugins (Placeholder for Phase 1 - we will verify plugin loader next)
    # kernel.load_plugins()

    # 4. Handle Mode
    if args.text:
        print(f"Server requested text execution: {args.text}")
        result = kernel.dispatch(args.text)
        print(f"Result: {result.message}")
        sys.exit(0 if result.success else 1)
    
    else:
        # Modo de Voz e UI
        print("--- Iniciando Jarvis (Modo Voz + UI) ---")
        
        # Verificar se a pasta do modelo existe
        if not os.path.exists("model"):
            print("❌ ERRO CRÍTICO: Modelo Vosk não encontrado.")
            # ... (mensagem de erro mantida)
            sys.exit(1)

        try:
            from core.voice_loop import VoiceLoop
            from core.voice_loop import VoiceLoop
            from ui.tray import SystemTray
            from ui.overlay import OverlayUI
            import threading
            
            # Iniciar Interface Overlay (Visual)
            overlay = OverlayUI(kernel)
            overlay.run()

            # Iniciar o Loop de Voz em uma Thread separada
            voice_loop = VoiceLoop(kernel)
            voice_thread = threading.Thread(target=voice_loop.start, daemon=True)
            voice_thread.start()
            
            # Iniciar System Tray na Thread Principal
            tray = SystemTray(kernel)
            tray.run()
            
        except ImportError as e:
            print(f"Erro de importação: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Erro inesperado: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
