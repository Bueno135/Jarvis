from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class CommandContext:
    """
    Context passed to a command execution.
    Contains the raw text, any parsed parameters, and the kernel instance.
    """
    raw_text: str
    command_name: str
    params: Dict[str, Any]
    # We avoid typing 'Kernel' here to prevent circular imports, 
    # but in practice it will be the Kernel instance.
    kernel: Any 

@dataclass
class CommandResult:
    """
    Standardized result for any command execution.
    """
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class PluginBase(ABC):
    """
    Base class that all plugins must inherit from.
    Enforces a strict contract for safety and predictability.
    """
    
    @abstractmethod
    def name(self) -> str:
        """
        Unique name of the plugin.
        """
        pass

    @abstractmethod
    def patterns(self) -> List[str]:
        """
        List of regex patterns or keywords this plugin handles.
        Example: ["open {app}", "launch {app}"]
        """
        pass

    @abstractmethod
    def execute(self, ctx: CommandContext) -> CommandResult:
        """
        Execute the command logic.
        Must return a CommandResult.
        """
        pass

class IntentParser(ABC):
    """
    Protocol for parsing raw text into a structured intent.
    """
    @abstractmethod
    def parse(self, text: str) -> Optional[CommandContext]:
        pass

class SpeechToText(ABC):
    """
    Protocol for Speech Recognition engines.
    """
    @abstractmethod
    def transcribe(self, audio: bytes) -> str:
        """
        Transcribes raw audio bytes to text.
        """
        pass
