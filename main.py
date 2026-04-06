import argparse
import sys
import yaml
import os
from core.kernel import Kernel, SystemState
from core.interfaces import CommandResult
from core.config_validator import validate_config, validate_environment, ConfigValidationError


def load_config(path="config/config.yaml"):
    """Load and validate configuration from YAML file."""
    raw_config = {}
    
    if not os.path.exists(path):
        print(f"Config file not found at {path}. Using defaults.")
    else:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            sys.exit(1)
    
    # Validate and normalize config
    try:
        config, warnings = validate_config(raw_config)
        for warning in warnings:
            print(f"\u26a0\ufe0f  Config warning: {warning}")
    except ConfigValidationError as e:
        print(f"\u274c Config error: {e}")
        sys.exit(1)
    
    # Check environment requirements
    env_warnings = validate_environment(config)
    for warning in env_warnings:
        print(f"\u26a0\ufe0f  Environment warning: {warning}")
    
    return config


def main():
    parser = argparse.ArgumentParser(description="Jarvis - Local Voice Assistant")
    parser.add_argument("--text", type=str, help="Run a text command directly and exit")
    parser.add_argument("--validate-config", action="store_true", help="Validate config and exit")
    args = parser.parse_args()

    # 1. Load and Validate Config
    config = load_config()
    
    if args.validate_config:
        print("\u2705 Configuration is valid.")
        sys.exit(0)

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
            print("Por favor, baixe um modelo de https://alphacephei.com/vosk/models")
            print("e extraia-o na pasta 'model/' do projeto.")
            sys.exit(1)

        try:
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
