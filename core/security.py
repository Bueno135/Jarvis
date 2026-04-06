import yaml
import os
import re
import fnmatch
from typing import List, Dict, Any, Set
from enum import Enum
from .logger import setup_logger


# Dangerous commands/patterns that should NEVER be allowed
DANGEROUS_PATTERNS = [
    r'rm\s+-rf',
    r'del\s+/[sfq]',
    r'format\s+[a-z]:',
    r'rd\s+/s',
    r'rmdir\s+/s',
    r':(){:|:&};:',  # Fork bomb
    r'>(\s*/dev/sd|\\\\\.\\.)',  # Direct disk write
    r'reg\s+(delete|add)',
    r'shutdown',
    r'taskkill\s+/f',
]


class AutonomyMode(Enum):
    """Autonomy levels for shell command execution."""
    MANUAL = "manual"           # All actions require confirmation
    SEMI_AUTO = "semi_auto"     # Whitelisted auto-execute, others need confirmation
    AUTONOMOUS = "autonomous"   # All non-dangerous auto-execute


class SecurityManager:
    """
    Gerencia políticas de segurança, listas de permissão (whitelists) e confirmações do usuário.
    Supports:
    - Exact match: "echo hello"
    - Prefix match: "echo *" (matches any echo command)
    - Glob patterns: "git *" (matches git commands)
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger("Jarvis.Security", config)
        self.whitelist: List[str] = []
        self.whitelist_prefixes: List[str] = []
        self._dangerous_regex = [re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS]

        # Initialize autonomy mode
        try:
            mode_str = config.get("security", {}).get("autonomy_mode", "manual")
            self.autonomy_mode = AutonomyMode(mode_str)
        except ValueError:
            self.logger.warning(f"Invalid autonomy mode '{mode_str}', defaulting to MANUAL")
            self.autonomy_mode = AutonomyMode.MANUAL

        self._load_whitelist()

    def _load_whitelist(self):
        path = "config/whitelist.yaml"
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                    raw_list = data.get("allowed_commands", [])

                    # Separate exact matches from prefix/glob patterns
                    for item in raw_list:
                        if '*' in item or '?' in item:
                            self.whitelist_prefixes.append(item)
                        else:
                            self.whitelist.append(item)

                    total = len(self.whitelist) + len(self.whitelist_prefixes)
                    self.logger.info(f"Loaded {total} allowed commands ({len(self.whitelist_prefixes)} patterns).")
            except yaml.YAMLError as e:
                self.logger.error(f"Error parsing whitelist.yaml: {e}")
        else:
            self.logger.warning("whitelist.yaml not found. Shell commands will be blocked.")

    def set_autonomy_mode(self, mode: AutonomyMode) -> None:
        """Set the autonomy mode for shell command execution."""
        self.autonomy_mode = mode
        self.logger.info(f"Autonomy mode changed to: {mode.value}")

    def get_autonomy_mode(self) -> AutonomyMode:
        """Get the current autonomy mode."""
        return self.autonomy_mode

    def _is_dangerous(self, command: str) -> bool:
        """
        Check if command matches any dangerous pattern.
        """
        for pattern in self._dangerous_regex:
            if pattern.search(command):
                return True
        return False

    def _matches_whitelist(self, command: str) -> bool:
        """
        Check if command matches whitelist (exact or pattern).
        """
        # Exact match
        if command in self.whitelist:
            return True
        
        # Check prefix/glob patterns
        for pattern in self.whitelist_prefixes:
            if fnmatch.fnmatch(command, pattern):
                return True
            # Also check if pattern matches just the command name (first word)
            cmd_name = command.split()[0] if command else ""
            if fnmatch.fnmatch(cmd_name, pattern.split()[0] if pattern else ""):
                # Pattern matched command name, check full pattern
                if fnmatch.fnmatch(command, pattern):
                    return True
        
        return False

    def can_execute_shell(self, command: str) -> bool:
        """
        Verifica se um comando shell é permitido based on autonomy mode.
        1. Always blocks dangerous patterns
        2. Behavior depends on autonomy_mode:
           - MANUAL: all non-dangerous commands require confirmation
           - SEMI_AUTO: whitelisted commands auto-execute, others need confirmation
           - AUTONOMOUS: all non-dangerous commands auto-execute
        """
        if not command or not command.strip():
            self.logger.warning("BLOCKED: Empty command")
            return False

        command = command.strip()

        # Always block dangerous commands
        if self._is_dangerous(command):
            self.logger.warning(f"BLOCKED dangerous command: {command}")
            return False

        # Check against autonomy mode
        is_whitelisted = self._matches_whitelist(command)

        if self.autonomy_mode == AutonomyMode.MANUAL:
            # MANUAL: always require confirmation
            return self.require_confirmation(f"Shell command: {command}")

        elif self.autonomy_mode == AutonomyMode.SEMI_AUTO:
            # SEMI_AUTO: whitelisted auto-execute, others need confirmation
            if is_whitelisted:
                self.logger.debug(f"ALLOWED shell command (whitelisted): {command}")
                return True
            else:
                return self.require_confirmation(f"Shell command (not whitelisted): {command}")

        elif self.autonomy_mode == AutonomyMode.AUTONOMOUS:
            # AUTONOMOUS: all non-dangerous auto-execute
            self.logger.debug(f"ALLOWED shell command (autonomous mode): {command}")
            return True

        # Fallback (should not reach here)
        self.logger.warning(f"BLOCKED shell command (unknown autonomy mode): {command}")
        return False

    def require_confirmation(self, action_description: str) -> bool:
        """
        Solicita confirmação do usuário (CLI ou Voz).
        Para a Fase 2 (Apenas Texto), usamos input().
        """
        if not self.config.get("security", {}).get("require_confirmation", True):
            return True

        print(f"⚠️  AVISO DE SEGURANÇA: Esta ação requer confirmação.")
        print(f"Ação: {action_description}")
        
        try:
            response = input("Deseja prosseguir? (s/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            self.logger.info(f"Confirmation interrupted for: {action_description}")
            return False
        
        if response in ('s', 'y', 'sim', 'yes'):
            self.logger.info(f"User CONFIRMED action: {action_description}")
            return True
        else:
            self.logger.info(f"User DENIED action: {action_description}")
            return False
