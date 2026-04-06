# Jarvis API Documentation

## Overview

Jarvis is a modular voice assistant system with a plugin-based architecture. This document describes the core APIs and interfaces for extending and integrating with Jarvis.

## Table of Contents

- [Core Components](#core-components)
- [Plugin Development](#plugin-development)
- [Configuration](#configuration)
- [Exception Handling](#exception-handling)
- [Memory System](#memory-system)
- [Audio System](#audio-system)
- [Security](#security)

---

## Core Components

### Kernel

The central orchestrator of the Jarvis system.

#### Class: `Kernel`

```python
class Kernel:
    def __init__(self, config: Dict[str, Any])
    def dispatch(self, text: str) -> CommandResult
    def speak(self, text: str) -> None
    def register_plugin(self, plugin: PluginBase) -> None
    def get_service(self, name: str) -> Any
    def set_state(self, new_state: SystemState) -> None
```

#### Methods

##### `dispatch(text: str) -> CommandResult`
Execute a command and return the result.

**Parameters:**
- `text`: Raw command text

**Returns:** `CommandResult` object

**Example:**
```python
from core.kernel import Kernel
from main import load_config

config = load_config()
kernel = Kernel(config)

result = kernel.dispatch("echo hello world")
print(result.message)  # "Echo: hello world"
```

##### `speak(text: str) -> None`
Convert text to speech using the registered TTS service.

**Parameters:**
- `text`: Text to speak

##### `register_plugin(plugin: PluginBase) -> None`
Register a new plugin with the kernel.

**Parameters:**
- `plugin`: Plugin instance

---

### Interfaces

#### CommandContext

Context passed to plugin execution.

```python
@dataclass
class CommandContext:
    raw_text: str
    command_name: str
    params: Dict[str, Any]
    kernel: Any
```

#### CommandResult

Standard result for command execution.

```python
@dataclass
class CommandResult:
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
```

#### PluginBase

Abstract base class for all plugins.

```python
class PluginBase(ABC):
    @abstractmethod
    def name(self) -> str: pass
    
    @abstractmethod
    def patterns(self) -> List[str]: pass
    
    @abstractmethod
    def execute(self, ctx: CommandContext) -> CommandResult: pass
```

---

## Plugin Development

### Creating a Plugin

1. **Inherit from BasePlugin** (recommended) or PluginBase
2. **Implement required methods**
3. **Place in plugins directory**

#### Basic Plugin Example

```python
from plugins.base_plugin import BasePlugin
from core.interfaces import CommandContext, CommandResult

class MyPlugin(BasePlugin):
    def name(self) -> str:
        return "MyPlugin"
    
    def patterns(self) -> List[str]:
        return ["hello", "greet"]
    
    def _execute_impl(self, ctx: CommandContext) -> CommandResult:
        return CommandResult(
            success=True,
            message=f"Hello from {self.name()}!",
            data={"plugin": self.name()}
        )
```

#### Advanced Plugin with Validation

```python
from plugins.base_plugin import BasePlugin
from core.interfaces import CommandContext, CommandResult
from core.exceptions import ValidationError

class CalculatorPlugin(BasePlugin):
    def name(self) -> str:
        return "Calculator"
    
    def patterns(self) -> List[str]:
        return ["calculate", "math", "compute"]
    
    def validate_context(self, ctx: CommandContext) -> bool:
        """Validate that we have a mathematical expression."""
        return any(op in ctx.raw_text for op in ['+', '-', '*', '/'])
    
    def _execute_impl(self, ctx: CommandContext) -> CommandResult:
        try:
            # Extract and evaluate expression
            expression = self._extract_expression(ctx.raw_text)
            result = eval(expression)  # Be careful with eval in production!
            
            return CommandResult(
                success=True,
                message=f"Result: {result}",
                data={"expression": expression, "result": result}
            )
        except Exception as e:
            raise ValidationError(f"Invalid expression: {e}")
    
    def _extract_expression(self, text: str) -> str:
        """Extract mathematical expression from text."""
        # Simple extraction logic
        words = text.split()
        for word in words:
            if any(op in word for op in ['+', '-', '*', '/']):
                return word
        raise ValidationError("No mathematical expression found")
```

### Plugin Patterns

Patterns determine which commands your plugin handles.

#### Simple Keywords
```python
def patterns(self) -> List[str]:
    return ["echo", "say", "repeat"]
```

#### Regex Patterns
```python
def patterns(self) -> List[str]:
    return ["calculate (.+)", "math (.+)"]
```

#### Parameterized Patterns
```python
def patterns(self) -> List[str]:
    return ["open {app}", "launch {app}", "start {app}"]
```

---

## Configuration

### Configuration Structure

```yaml
app:
  name: "Jarvis"
  version: "0.1.0"
  language: "pt-BR"
  wake_word: "jarvis"

logging:
  level: "INFO"
  file: "logs/jarvis.json"
  console: true

security:
  command_whitelist: []
  require_confirmation: true
  autonomy_mode: "semi_auto"

memory:
  max_entries: 50
  persist_path: "data/memory"

ai:
  provider: "gemini"
  api_key_env: "GEMINI_API_KEY"
  timeout: 10
  enabled: true

stt:
  provider: "whisper"
  model: "openai/whisper-tiny"
  language: "pt"
  device: "cpu"
  sample_rate: 16000

tts:
  voice: "pt-BR-AntonioNeural"
  rate: "+0%"

vad:
  energy_threshold: 300
  silence_timeout_speech: 1.0
  silence_timeout_no_speech: 5.0
  max_buffer_seconds: 15
```

### Loading Configuration

```python
from main import load_config

config = load_config()
print(config["app"]["name"])  # "Jarvis"
```

### Validating Configuration

```python
from core.config_validator import validate_config

config, warnings = validate_config(raw_config)
if warnings:
    for warning in warnings:
        print(f"Warning: {warning}")
```

---

## Exception Handling

### Custom Exceptions

Jarvis provides specific exception types for better error handling:

```python
from core.exceptions import (
    PluginError, SecurityError, STTError, TTSError,
    MemoryError, AudioError, ValidationError
)

# Raise specific exceptions
raise PluginError("Failed to process command", "MyPlugin")
raise SecurityError("Dangerous command detected", command="rm -rf /")
raise ValidationError("Invalid input", field="username", value="abc123")
```

### Exception Handling Decorator

Use the `@handle_exception` decorator for standardized error handling:

```python
from core.exceptions import handle_exception

@handle_exception
def my_function():
    # Function logic here
    pass
```

---

## Memory System

### Short-Term Memory

For session-based memory storage.

```python
from core.memory.short_term import ShortTermMemory
from core.interfaces import MemoryEntry

# Initialize
memory = ShortTermMemory(max_entries=50)

# Store entry
entry = MemoryEntry(
    id="1",
    content="User asked about weather",
    metadata={"type": "question", "timestamp": time.time()}
)
memory.store(entry)

# Query memory
results = memory.query("weather", k=5)
for result in results:
    print(result.content)
```

### Long-Term Memory

For persistent memory storage (requires ChromaDB).

```python
from core.memory.long_term import LongTermMemory

# Initialize
memory = LongTermMemory(persist_path="data/memory")

# Store and query similar to short-term memory
memory.store(entry)
results = memory.query("weather", k=10)
```

---

## Audio System

### Enhanced Audio Manager

```python
from core.enhanced_audio import EnhancedAudioManager

# Initialize
audio_manager = EnhancedAudioManager(config)

# Ensure models are available
audio_manager.ensure_stt_model()

# Get device information
device_info = audio_manager.get_audio_device_info()
print(f"Found {device_info['input_devices']} input devices")

# Test audio input
test_result = audio_manager.test_audio_input(duration=2)
print(f"Audio level: {test_result['audio_level']}")
```

### Audio Settings

```python
# Get optimal settings
settings = audio_manager.get_optimal_settings()
print(f"Sample rate: {settings['sample_rate']}")
print(f"Chunk size: {settings['chunk_size']}")
```

---

## Security

### Security Manager

```python
from core.security import SecurityManager, AutonomyMode

# Initialize
security = SecurityManager(config)

# Validate command
from core.interfaces import CommandContext
ctx = CommandContext(
    raw_text="echo hello",
    command_name="Echo",
    params={},
    kernel=None
)

result = security.validate_command(ctx)
if result.success:
    print("Command is safe to execute")
else:
    print(f"Command blocked: {result.message}")

# Check if confirmation is required
if security.requires_confirmation(ctx):
    response = input("Execute this command? (y/n): ")
    if response.lower() != 'y':
        print("Command cancelled")
```

### Autonomy Modes

```python
from core.security import AutonomyMode

# Set autonomy mode
security.set_autonomy_mode(AutonomyMode.SEMI_AUTO)

# Check current mode
current_mode = security.get_autonomy_mode()
print(f"Current mode: {current_mode.value}")
```

### Command Whitelist

Create `config/whitelist.yaml`:

```yaml
allowed_commands:
  - "echo *"
  - "date"
  - "time"
  - "weather"
  - "notepad"
  - "calculator"
```

---

## UI System

### UI Manager

```python
from ui.ui_manager import UIManager

# Initialize
ui_manager = UIManager(kernel)

# Show notification
ui_manager.show_notification("Success", "Command completed")

# Update status
ui_manager.update_status("Processing...", "processing")

# Get user input
user_input = ui_manager.get_user_input("Enter your name:")
```

---

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_integration_real.py

# Run with coverage
python -m pytest --cov=core tests/

# Run specific test markers
python -m pytest -m "unit" tests/
python -m pytest -m "integration" tests/
```

### Test Fixtures

```python
def test_my_plugin(mock_kernel, mock_command_context):
    """Test using fixtures from conftest.py"""
    plugin = MyPlugin()
    result = plugin.execute(mock_command_context)
    assert result.success is True
```

---

## Best Practices

### 1. Error Handling
- Use specific exception types
- Implement proper validation
- Use the `@handle_exception` decorator

### 2. Logging
- Use the provided logger: `self.logger = logging.getLogger("Jarvis.MyPlugin")`
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)

### 3. Plugin Design
- Keep plugins focused and single-purpose
- Validate input before processing
- Return structured CommandResult objects
- Use BasePlugin for common functionality

### 4. Configuration
- Validate configuration values
- Provide sensible defaults
- Document all configuration options

### 5. Security
- Always validate user input
- Use the security manager for dangerous operations
- Implement proper access controls

---

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Check dependencies
   python -c "import core.kernel"
   ```

2. **Plugin Not Loading**
   ```python
   # Check plugin structure
   from core.plugin_loader import PluginLoader
   loader = PluginLoader()
   plugins = loader.discover_and_load()
   print([p.name() for p in plugins])
   ```

3. **Audio Issues**
   ```python
   # Test audio system
   from core.enhanced_audio import EnhancedAudioManager
   audio = EnhancedAudioManager(config)
   audio.test_audio_input()
   ```

### Debug Mode

Enable debug logging:

```yaml
logging:
  level: "DEBUG"
```

Or set environment variable:

```bash
export JARVIS_LOG_LEVEL=DEBUG
```

---

## Contributing

When contributing to Jarvis:

1. Follow the existing code style
2. Add tests for new functionality
3. Update documentation
4. Use the provided exception handling
5. Follow security best practices

For more detailed information, see the [CONTRIBUTING.md](CONTRIBUTING.md) file.
