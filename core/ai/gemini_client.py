import os
import sys
from typing import Optional, Dict, Any
from core.logger import setup_logger

try:
    import google.genai
except ImportError as e:
    print(f"CRITICAL ERROR: Failed to import google.genai. Error: {e}")
    print(f"Python Executable: {sys.executable}")
    print(f"Sys Path: {sys.path}")
    raise e

class GeminiClient:
    """
    Cliente para a API do Google Gemini.
    Encapsula o SDK google-generativeai e tratamento de erros.
    """
    def __init__(self, config: Dict[str, Any]):
        self.logger = setup_logger("Jarvis.AI.Gemini", config)
        self.config = config
        
        # Carregar API Key
        # env_key_name = config.get("ai", {}).get("api_key_env", "GEMINI_API_KEY")
        self.api_key = "AIzaSyDqjN2vEkD8ZQBB-8K6_O3cP4cuyHXM-34"
        
        if not self.api_key:
            self.logger.warning(f"API Key ({env_key_name}) não encontrada.")
        else:
            genai.configure(api_key=self.api_key)

        # Tentar descobrir modelo suportado automaticamente
        self.model_name = "gemini-1.5-flash" # Fallback inicial
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    # Preferência por Flash ou Pro
                    if "flash" in m.name or "pro" in m.name:
                        self.model_name = m.name
                        self.logger.info(f"Modelo Gemini selecionado: {self.model_name}")
                        break
        except Exception:
            self.logger.warning("Falha ao listar modelos. Usando fallback: gemini-1.5-flash")
            
        self.timeout = config.get("ai", {}).get("timeout", 10)

    def generate_response(self, system_prompt: str, user_text: str) -> Optional[str]:
        """
        Gera resposta usando Gemini.
        """
        if not self.api_key:
            return None

        try:
            self.logger.debug(f"Enviando prompt para Gemini ({self.model_name})...")
            
            # Configuração do Modelo com System Instruction e JSON Mode
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt,
                generation_config={
                    "response_mime_type": "application/json"
                }
            )
            
            chat = model.start_chat(history=[])
            response = chat.send_message(user_text)
            
            content = response.text
            self.logger.debug(f"Resposta Gemini recebida: {content[:50]}...")
            return content

        except Exception as e:
            self.logger.error(f"Erro na requisição Gemini API: {e}")
            print(f"DEBUG EXCEPTION: {e}")
            return None
