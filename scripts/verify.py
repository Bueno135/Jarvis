import sys
import time
from core.kernel import Kernel, SystemState

def verify_pipeline():
    print("--- Verificação do Pipeline Jarvis ---")
    
    # 1. Inicializar Kernel
    print("[1] Inicializando Kernel...")
    kernel = Kernel({"logging": {"level": "DEBUG"}, "security": {"require_confirmation": False}})
    if kernel.state == SystemState.IDLE:
        print("✅ Kernel IDLE")
    else:
        print("❌ Kernel Status Erro")

    # 2. Verificar Plugins
    print("\n[2] Verificando Plugins...")
    plugins = kernel.plugins
    print(f"Plugins carregados: {list(plugins.keys())}")
    
    required = ["OpenApp", "FileOps", "RunShell"]
    missing = [p for p in required if p not in plugins]
    
    if not missing:
        print("✅ Todos os plugins críticos carregados.")
    else:
        print(f"❌ Faltando plugins: {missing}")

    # 3. Simular Pipeline de Voz (Mock)
    print("\n[3] Simulando Comando de Voz 'echo Olá Jarvis'...")
    
    # Simula o que o VoiceLoop faria: dispatch(text)
    kernel.set_state(SystemState.LISTENING)
    result = kernel.dispatch("echo Olá Jarvis")
    
    if result.success and "Olá Jarvis" in result.message:
        print(f"✅ Comando executado com sucesso: {result.message}")
    else:
        print(f"❌ Falha na execução: {result.message}")

    # 4. Simular Comando de Segurança
    print("\n[4] Simulando Comando Bloqueado 'run rm -rf /'...")
    result_sec = kernel.dispatch("run rm -rf /")
    
    print(f"DEBUG: Success={result_sec.success}, Message='{result_sec.message}'")

    if not result_sec.success and "BLOCKED" in result_sec.message:
        print(f"✅ Bloqueio de segurança funcionou: {result_sec.message}")
    else:
        print(f"❌ Falha na segurança (Comando devia ser bloqueado).")

    print("\n--- Verificação Concluída ---")

if __name__ == "__main__":
    verify_pipeline()
