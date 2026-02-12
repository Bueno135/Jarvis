import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from core.interfaces import CommandContext
from core.logger import setup_logger
from .gemini_client import GeminiClient

# TODO: Mover para core/interfaces.py se precisar ser reutilizável por outros resolvers
class IntentResolver(ABC):
    @abstractmethod
    def resolve(self, text: str) -> Optional[Dict[str, Any]]:
        pass

class AIIntentResolver(IntentResolver):
    """
    Resolvedor de intenção baseado em IA (Gemini).
    Atua como fallback quando o sistema baseada em regras falha.
    """
    def __init__(self, kernel):
        self.kernel = kernel
        self.config = kernel.config
        self.logger = setup_logger("Jarvis.AI.Resolver", self.config)
        self.client = GeminiClient(self.config)
        
        # Blacklist de palavras perigosas para validação pré-envio/pós-recebimento
        self.blacklist = ["rm ", "del ", "format ", "shutdown", "reg ", "system32"]

    def resolve(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Analisa o texto e retorna a intenção estruturada ou None.
        """
        # 1. Validação de Segurança Básica (Blacklist) no input
        if any(bad in text.lower() for bad in self.blacklist):
            self.logger.warning(f"Texto contém palavras proibidas. Abortando IA: {text}")
            return None

        # 2. Construir System Prompt
        system_prompt = self._get_system_prompt()

        # 3. Chamar API
        self.logger.info(f"Consultando IA para: '{text}'")
        raw_response = self.client.generate_response(text, system_instruction=system_prompt)
        
        if not raw_response:
            return None

        # 4. Parse e Validação
        try:
            # O client já retorna um dicionário (JSON parseado)
            data = raw_response
            
            intent = data.get("intent")
            if not intent or intent == "unknown":
                self.logger.info("IA não identificou intenção clara (unknown).")
                return None
                
            self.logger.info(f"IA identificou intenção: {intent}")
            
            # Validação extra de segurança nos parâmetros
            if "parameters" in data:
                for key, value in data["parameters"].items():
                    if isinstance(value, str) and any(bad in value.lower() for bad in self.blacklist):
                         self.logger.warning(f"Parâmetro da IA inseguro: {value}. Bloqueando.")
                         return None
                         
            return data

        except json.JSONDecodeError:
            self.logger.error("IA retornou JSON inválido.")
        except Exception as e:
            self.logger.error(f"Erro ao processar resposta da IA: {e}")
            
        return None

    def _get_system_prompt(self) -> str:
        """
        Retorna o prompt de sistema rigoroso.
        """
        return """You are an intent classification engine for a local automation assistant.

You must ONLY return valid JSON.

Never explain.
Never add text.
Never wrap in markdown.
Only output raw JSON.

Possible intents:
open_app
create_file
write_text
run_shell
question
unknown

For command intents, return:
{
"intent": "intent_name",
"parameters": { ... }
}

For questions:
{
"intent": "question",
"response": "short concise answer"
}

If the user input is not a command, you MUST reply as a helpful assistant.
{
"intent": "question",
"response": "your helpful answer here"
}

If you really cannot help or understand:
{
"intent": "unknown"
}

User text:
"{USER_TEXT}"
"""
