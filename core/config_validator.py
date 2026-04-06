"""
Configuration validation for Jarvis.
Ensures config.yaml has required fields and valid values.
"""
from typing import Dict, Any, List, Optional, Tuple
import os


class ConfigValidationError(Exception):
    """Raised when config validation fails."""
    pass


# Schema definition: field -> (type, required, default, validator_func)
CONFIG_SCHEMA = {
    "app": {
        "name": (str, False, "Jarvis", None),
        "version": (str, False, "0.1.0", None),
        "language": (str, False, "en-US", None),
        "wake_word": (str, False, "jarvis", None),
    },
    "logging": {
        "level": (str, False, "INFO", lambda v: v.upper() in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")),
        "file": (str, False, "logs/jarvis.json", None),
        "console": (bool, False, True, None),
    },
    "security": {
        "command_whitelist": (list, False, [], None),
        "require_confirmation": (bool, False, True, None),
    },
    "ai": {
        "provider": (str, False, "gemini", lambda v: v in ("gemini", "openai", "local")),
        "api_key_env": (str, False, "GEMINI_API_KEY", None),
        "timeout": (int, False, 10, lambda v: 1 <= v <= 120),
        "enabled": (bool, False, True, None),
    },
    "stt": {
        "provider": (str, False, "whisper", lambda v: v in ("whisper", "vosk")),
        "model": (str, False, "openai/whisper-tiny", None),
        "language": (str, False, "en", None),
        "device": (str, False, "cpu", lambda v: v in ("cpu", "cuda", "mps")),
    },
    "tts": {
        "voice": (str, False, "pt-BR-AntonioNeural", None),
        "rate": (str, False, "+0%", None),
    },
}


def validate_config(config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validates and normalizes configuration.
    
    Args:
        config: Raw config dictionary from YAML
        
    Returns:
        Tuple of (normalized_config, warnings)
        
    Raises:
        ConfigValidationError: If required field is missing or invalid
    """
    if config is None:
        config = {}
    
    warnings = []
    normalized = {}
    
    for section_name, section_schema in CONFIG_SCHEMA.items():
        section_data = config.get(section_name, {})
        if section_data is None:
            section_data = {}
        
        normalized[section_name] = {}
        
        for field_name, (expected_type, required, default, validator) in section_schema.items():
            value = section_data.get(field_name)
            
            # Check if required field is missing
            if value is None:
                if required:
                    raise ConfigValidationError(
                        f"Required config field '{section_name}.{field_name}' is missing"
                    )
                value = default
                
            # Type validation
            if value is not None and not isinstance(value, expected_type):
                # Try to coerce types
                try:
                    if expected_type == bool and isinstance(value, str):
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    elif expected_type == int and isinstance(value, (str, float)):
                        value = int(value)
                    elif expected_type == str and not isinstance(value, str):
                        value = str(value)
                    else:
                        raise ConfigValidationError(
                            f"Config field '{section_name}.{field_name}' expected {expected_type.__name__}, "
                            f"got {type(value).__name__}"
                        )
                except (ValueError, TypeError) as e:
                    raise ConfigValidationError(
                        f"Config field '{section_name}.{field_name}' type conversion failed: {e}"
                    )
            
            # Custom validation
            if validator and value is not None:
                if not validator(value):
                    warnings.append(
                        f"Config field '{section_name}.{field_name}' has suspicious value: {value}"
                    )
            
            normalized[section_name][field_name] = value
    
    # Preserve any extra fields not in schema (for extensibility)
    for section_name, section_data in config.items():
        if section_name not in normalized:
            normalized[section_name] = section_data
        elif isinstance(section_data, dict):
            for field_name, value in section_data.items():
                if field_name not in normalized[section_name]:
                    normalized[section_name][field_name] = value
    
    return normalized, warnings


def validate_environment(config: Dict[str, Any]) -> List[str]:
    """
    Validates environment requirements based on config.
    
    Returns:
        List of warning messages
    """
    warnings = []
    
    # Check AI API key if AI is enabled
    ai_config = config.get("ai", {})
    if ai_config.get("enabled", True):
        api_key_env = ai_config.get("api_key_env", "GEMINI_API_KEY")
        if not os.environ.get(api_key_env):
            warnings.append(
                f"AI is enabled but environment variable '{api_key_env}' is not set. "
                f"AI features may not work."
            )
    
    # Check STT device
    stt_config = config.get("stt", {})
    if stt_config.get("device") == "cuda":
        try:
            import torch
            if not torch.cuda.is_available():
                warnings.append("STT device is 'cuda' but CUDA is not available. Falling back to CPU.")
        except ImportError:
            warnings.append("STT device is 'cuda' but torch is not installed.")
    
    return warnings
