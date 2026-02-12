import os
from google.genai import Client
from typing import Optional, Dict, Any
import json
from core.logger import setup_logger

class GeminiClient:
    """
    Cliente para a API do Google Gemini (SDK google-genai).
    """
    def __init__(self, config: Dict[str, Any]):
        self.logger = setup_logger("Jarvis.AI.Gemini", config)
        
        # Carregar API Key
        # env_key_name = config.get("ai", {}).get("api_key_env", "GEMINI_API_KEY")
        self.api_key = "AIzaSyDqjN2vEkD8ZQBB-8K6_O3cP4cuyHXM-34"
        
        if not self.api_key:
            self.logger.warning(f"API Key ({api_key_env}) não encontrada no ambiente.")
            self.client = None
        else:
            try:
                self.client = Client(api_key=self.api_key)
                self.logger.info("Cliente Gemini (google-genai) inicializado.")
            except Exception as e:
                self.logger.error(f"Erro ao inicializar cliente Gemini: {e}")
                self.client = None

        self.model_name = config.get("ai", {}).get("model", "gemini-2.0-flash") 

    def generate_response(self, prompt: str, image: Optional[Any] = None, system_instruction: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if not self.client:
            self.logger.warning("Cliente Gemini não está pronto.")
            return None

        self.logger.debug(f"Enviando prompt para Gemini ({self.model_name})...")

        try:
            # Configurar config do request
            config_params = {
                'response_mime_type': 'application/json'
            }
            if system_instruction:
                config_params['system_instruction'] = system_instruction
            
            # Prepare contents
            contents = [prompt]
            if image:
                 self.logger.info("Anexando imagem ao prompt...")
                 contents.append(image)

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config_params
            )
            
            if not response.text:
                self.logger.warning("Resposta vazia do Gemini.")
                return None

            try:
                # Limpar markdown ```json ... ``` se vier (o SDK geralmente manda puro se mime_type for json, mas garante)
                cleaned_text = response.text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                
                return json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                self.logger.error(f"Erro ao fazer parse do JSON: {e}. Texto recebido: {response.text}")
                return None

        except Exception as e:
            self.logger.error(f"Erro na requisição Gemini API: {e}")
            return None
