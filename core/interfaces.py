from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import time

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

class TextToSpeech(ABC):
    """
    Protocol for Text-to-Speech engines.
    """
    @abstractmethod
    def speak(self, text: str) -> None:
        """
        Synthesizes speech from text.
        """
        pass

    @abstractmethod
    def is_busy(self) -> bool:
        """
        Returns True if TTS is currently speaking.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        Stops current playback.
        """
        pass


class TaskStatus(Enum):
    """
    Enum for tracking the status of tasks and task steps.
    """
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass
class TaskStep:
    """
    Represents a single step in a task plan.
    """
    id: str
    description: str
    plugin_name: str
    params: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[CommandResult] = None


@dataclass
class TaskPlan:
    """
    Represents a multi-step plan to achieve a goal.
    """
    goal: str
    steps: List[TaskStep] = field(default_factory=list)
    current_step_index: int = 0
    status: TaskStatus = TaskStatus.PENDING


class TaskPlannerBase(ABC):
    """
    Abstract base class for task planning implementations.
    """
    @abstractmethod
    def plan(self, goal: str, available_plugins: List[str]) -> TaskPlan:
        """
        Generates a task plan to achieve the given goal.
        """
        pass


class MemoryEntryType(Enum):
    """
    Enum for types of memory entries.
    """
    SESSION = "session"
    PERSISTENT = "persistent"


@dataclass
class MemoryEntry:
    """
    Represents a single entry in the memory store.
    """
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    entry_type: MemoryEntryType = MemoryEntryType.SESSION


class MemoryStore(ABC):
    """
    Abstract base class for memory storage implementations.
    """
    @abstractmethod
    def store(self, entry: MemoryEntry) -> None:
        """
        Stores a memory entry.
        """
        pass

    @abstractmethod
    def query(self, text: str, k: int = 5) -> List[MemoryEntry]:
        """
        Queries the memory store for relevant entries.
        Returns the k most relevant entries.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clears all memory entries.
        """
        pass
