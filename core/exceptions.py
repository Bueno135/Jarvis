"""
Custom exceptions for Jarvis.
Provides specific exception types for better error handling and debugging.
"""

class JarvisException(Exception):
    """Base exception for Jarvis."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        
    def __str__(self):
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message

class ConfigurationError(JarvisException):
    """Configuration related errors."""
    pass

class PluginError(JarvisException):
    """Plugin related errors."""
    def __init__(self, message: str, plugin_name: str = None, details: dict = None):
        super().__init__(message, details)
        self.plugin_name = plugin_name
        
    def __str__(self):
        base_msg = super().__str__()
        if self.plugin_name:
            return f"[Plugin: {self.plugin_name}] {base_msg}"
        return base_msg

class STTError(JarvisException):
    """Speech-to-text errors."""
    def __init__(self, message: str, audio_length: int = None, provider: str = None, details: dict = None):
        super().__init__(message, details)
        self.audio_length = audio_length
        self.provider = provider
        
    def __str__(self):
        base_msg = super().__str__()
        info_parts = []
        if self.provider:
            info_parts.append(f"Provider: {self.provider}")
        if self.audio_length is not None:
            info_parts.append(f"Audio: {self.audio_length} bytes")
        
        if info_parts:
            return f"[STT] {base_msg} ({', '.join(info_parts)})"
        return f"[STT] {base_msg}"

class TTSError(JarvisException):
    """Text-to-speech errors."""
    def __init__(self, message: str, text_length: int = None, voice: str = None, details: dict = None):
        super().__init__(message, details)
        self.text_length = text_length
        self.voice = voice
        
    def __str__(self):
        base_msg = super().__str__()
        info_parts = []
        if self.voice:
            info_parts.append(f"Voice: {self.voice}")
        if self.text_length is not None:
            info_parts.append(f"Text: {self.text_length} chars")
        
        if info_parts:
            return f"[TTS] {base_msg} ({', '.join(info_parts)})"
        return f"[TTS] {base_msg}"

class SecurityError(JarvisException):
    """Security related errors."""
    def __init__(self, message: str, command: str = None, risk_level: str = None, details: dict = None):
        super().__init__(message, details)
        self.command = command
        self.risk_level = risk_level
        
    def __str__(self):
        base_msg = super().__str__()
        info_parts = []
        if self.risk_level:
            info_parts.append(f"Risk: {self.risk_level}")
        if self.command:
            info_parts.append(f"Command: {self.command[:50]}{'...' if len(self.command) > 50 else ''}")
        
        if info_parts:
            return f"[Security] {base_msg} ({', '.join(info_parts)})"
        return f"[Security] {base_msg}"

class MemoryError(JarvisException):
    """Memory system errors."""
    def __init__(self, message: str, memory_type: str = None, operation: str = None, details: dict = None):
        super().__init__(message, details)
        self.memory_type = memory_type
        self.operation = operation
        
    def __str__(self):
        base_msg = super().__str__()
        info_parts = []
        if self.memory_type:
            info_parts.append(f"Type: {self.memory_type}")
        if self.operation:
            info_parts.append(f"Operation: {self.operation}")
        
        if info_parts:
            return f"[Memory] {base_msg} ({', '.join(info_parts)})"
        return f"[Memory] {base_msg}"

class AudioError(JarvisException):
    """Audio system errors."""
    def __init__(self, message: str, device: str = None, sample_rate: int = None, details: dict = None):
        super().__init__(message, details)
        self.device = device
        self.sample_rate = sample_rate
        
    def __str__(self):
        base_msg = super().__str__()
        info_parts = []
        if self.device:
            info_parts.append(f"Device: {self.device}")
        if self.sample_rate:
            info_parts.append(f"Sample Rate: {self.sample_rate}")
        
        if info_parts:
            return f"[Audio] {base_msg} ({', '.join(info_parts)})"
        return f"[Audio] {base_msg}"

class ValidationError(JarvisException):
    """Validation errors for inputs and data."""
    def __init__(self, message: str, field: str = None, value: str = None, details: dict = None):
        super().__init__(message, details)
        self.field = field
        self.value = value
        
    def __str__(self):
        base_msg = super().__str__()
        info_parts = []
        if self.field:
            info_parts.append(f"Field: {self.field}")
        if self.value is not None:
            info_parts.append(f"Value: {str(self.value)[:50]}{'...' if len(str(self.value)) > 50 else ''}")
        
        if info_parts:
            return f"[Validation] {base_msg} ({', '.join(info_parts)})"
        return f"[Validation] {base_msg}"

# Utility function for exception handling
def handle_exception(func):
    """Decorator for standardized exception handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except JarvisException:
            # Re-raise Jarvis exceptions as-is
            raise
        except ImportError as e:
            raise JarvisException(f"Missing dependency: {e}", {"module": str(e).split("'")[1]})
        except PermissionError as e:
            raise SecurityError(f"Permission denied: {e}", {"operation": str(e)})
        except FileNotFoundError as e:
            raise ConfigurationError(f"File not found: {e}", {"file": str(e).split("'")[1]})
        except ValueError as e:
            raise ValidationError(f"Invalid value: {e}")
        except Exception as e:
            raise JarvisException(f"Unexpected error: {e}", {"type": type(e).__name__, "original": str(e)})
    return wrapper
