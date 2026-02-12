import google.generativeai as genai
from core.ai.gemini_client import GeminiClient

config = {
    "logging": {"level": "DEBUG"},
    "ai": {"timeout": 10}
}

print("--- Testando GeminiClient ---")
client = GeminiClient(config)

if not client.api_key:
    print("API Key nao configurada!")
    # exit(1) # Continue to debug environment

import sys
print(f"Test Env Python: {sys.executable}")
print(f"Test Env Path: {sys.path}")

print(f"API Key: {client.api_key[:5]}...")

print("--- Buscando Modelo Disponivel ---")
selected_model = None

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Modelo encontrado: {m.name}")
            selected_model = m.name
            break # Pega o primeiro e para
    
    if selected_model:
        print(f"--- Usando Modelo: {selected_model} ---")
        client.model_name = selected_model # Força o uso deste modelo
        
        response = client.generate_response(
            "You are a helpful assistant. Respond in JSON with {'status': 'ok'}", 
            "Say hello"
        )

        if response:
            print(f"Sucesso! Resposta: {response}")
        else:
            print("Falha na conexao (Generate retornou None).")
            
    else:
        print("Nenhum modelo compativel encontrado.")

except Exception as e:
    print(f"Erro fatal: {e}")
