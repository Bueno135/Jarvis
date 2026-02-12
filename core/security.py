import yaml
import os
from typing import List, Dict, Any
from .logger import setup_logger

class SecurityManager:
    """
    Gerencia políticas de segurança, listas de permissão (whitelists) e confirmações do usuário.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger("Jarvis.Security", config)
        self.whitelist: List[str] = []
        self._load_whitelist()

    def _load_whitelist(self):
        path = "config/whitelist.yaml"
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
                self.whitelist = data.get("allowed_commands", [])
                self.logger.info(f"Carregados {len(self.whitelist)} comandos permitidos.")
        else:
            self.logger.warning("whitelist.yaml não encontrado. Comandos de shell serão bloqueados.")

    def can_execute_shell(self, command: str) -> bool:
        """
        Verifica se um comando shell está na whitelist.
        Implementação básica: correspondência exata.
        """
        # Segurança: Correspondência exata para o MVP para evitar injeções ou comandos perigosos
        # "rm -rf /; echo allowed" não funcionaria se a whitelist tiver apenas "echo"
        is_allowed = command in self.whitelist
        
        if not is_allowed:
            self.logger.warning(f"BLOCKED comando shell: {command}")
        
        return is_allowed

    def require_confirmation(self, action_description: str) -> bool:
        """
        Solicita confirmação do usuário (CLI ou Voz).
        Para a Fase 2 (Apenas Texto), usamos input().
        """
        if not self.config.get("security", {}).get("require_confirmation", True):
            return True

        print(f"⚠️  AVISO DE SEGURANÇA: Esta ação requer confirmação.")
        print(f"Ação: {action_description}")
        response = input("Deseja prosseguir? (s/n): ").strip().lower()
        
        if response == 's' or response == 'y':  # Aceita 's' (sim) ou 'y' (yes)
            self.logger.info(f"Usuário CONFIRMOU ação: {action_description}")
            return True
        else:
            self.logger.info(f"Usuário NEGOU ação: {action_description}")
            return False
