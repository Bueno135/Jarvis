# Jarvis API Reference

## Table of Contents

- [Core API](#core-api)
  - [Kernel](#kernel)
  - [Plugin System](#plugin-system)
  - [Security](#security)
  - [Memory System](#memory-system)
  - [Audio System](#audio-system)
  - [AI Integration](#ai-integration)
- [Advanced Features](#advanced-features)
  - [Intelligent Cache](#intelligent-cache)
  - [Dynamic Plugin Loader](#dynamic-plugin-loader)
  - [Advanced NLP](#advanced-nlp)
  - [Task Scheduler](#task-scheduler)
  - [Continuous Learning](#continuous-learning)
  - [Web Interface](#web-interface)
- [Utilities](#utilities)
  - [Configuration](#configuration)
  - [Logging](#logging)
  - [Exceptions](#exceptions)
  - [Metrics](#metrics)
- [Examples](#examples)

---

## Core API

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
    def get_plugin(self, name: str) -> Optional[PluginBase]
    def list_plugins(self) -> List[str]
    def shutdown(self) -> None
```

#### Methods

##### `__init__(config: Dict[str, Any])`
Initialize the kernel with configuration.

**Parameters:**
- `config`: Configuration dictionary

**Example:**
```python
from main import load_config
from core.kernel import Kernel

config = load_config()
kernel = Kernel(config)
```

##### `dispatch(text: str) -> CommandResult`
Execute a command and return the result.

**Parameters:**
- `text`: Raw command text

**Returns:** `CommandResult` object

**Example:**
```python
result = kernel.dispatch("echo hello world")
print(result.message)  # "Echo: hello world"
print(result.success)  # True
```

##### `speak(text: str) -> None`
Convert text to speech using the registered TTS service.

**Parameters:**
- `text`: Text to speak

**Example:**
```python
kernel.speak("Hello, world!")
```

##### `register_plugin(plugin: PluginBase) -> None`
Register a new plugin with the kernel.

**Parameters:**
- `plugin`: Plugin instance

**Example:**
```python
from plugins.system.echo import EchoPlugin

plugin = EchoPlugin()
kernel.register_plugin(plugin)
```

##### `get_service(name: str) -> Any`
Get a registered service by name.

**Parameters:**
- `name`: Service name

**Returns:** Service instance or None

**Example:**
```python
security = kernel.get_service("security")
if security:
    print("Security service available")
```

##### `set_state(new_state: SystemState) -> None`
Set the system state.

**Parameters:**
- `new_state`: New system state

**Example:**
```python
from core.kernel import SystemState
kernel.set_state(SystemState.PROCESSING)
```

---

### Plugin System

#### Base Class: `PluginBase`

```python
class PluginBase(ABC):
    @abstractmethod
    def name(self) -> str: pass
    
    @abstractmethod
    def patterns(self) -> List[str]: pass
    
    @abstractmethod
    def execute(self, ctx: CommandContext) -> CommandResult: pass
```

#### Enhanced Base Class: `BasePlugin`

```python
class BasePlugin(PluginBase):
    def validate_context(self, ctx: CommandContext) -> bool
    def get_help(self) -> str
    def cleanup(self) -> None
    def _execute_impl(self, ctx: CommandContext) -> CommandResult
    def log_execution(self, ctx: CommandContext, result: CommandResult)
    def get_plugin_info(self) -> Dict[str, Any]
```

#### Plugin Loader

```python
class PluginLoader:
    def __init__(self, config: Dict[str, Any] = None)
    def discover_and_load(self) -> List[PluginBase]
    def load_plugin(self, plugin_path: str) -> Optional[PluginBase]
    def validate_plugin(self, plugin: PluginBase) -> bool
    def get_plugin_info(self, plugin: PluginBase) -> Dict[str, Any]
```

---

### Security

#### Class: `SecurityManager`

```python
class SecurityManager:
    def __init__(self, config: Dict[str, Any])
    def can_execute_shell(self, command: str) -> bool
    def require_confirmation(self, action_description: str) -> bool
    def validate_command(self, ctx: CommandContext) -> CommandResult
    def set_autonomy_mode(self, mode: AutonomyMode) -> None
    def get_autonomy_mode(self) -> AutonomyMode
    def add_to_whitelist(self, pattern: str) -> None
    def remove_from_whitelist(self, pattern: str) -> None
```

#### Methods

##### `can_execute_shell(command: str) -> bool`
Check if a shell command can be executed.

**Parameters:**
- `command`: Shell command to check

**Returns:** True if command is safe to execute

**Example:**
```python
security = SecurityManager(config)
if security.can_execute_shell("echo hello"):
    os.system("echo hello")
```

##### `validate_command(ctx: CommandContext) -> CommandResult`
Validate a command context.

**Parameters:**
- `ctx`: Command context to validate

**Returns:** CommandResult indicating validation result

**Example:**
```python
from core.interfaces import CommandContext

ctx = CommandContext(
    raw_text="rm -rf /",
    command_name="RunShell",
    params={},
    kernel=None
)

result = security.validate_command(ctx)
if not result.success:
    print(f"Command blocked: {result.message}")
```

---

### Memory System

#### Short-term Memory

```python
class ShortTermMemory:
    def __init__(self, max_entries: int = 50)
    def store(self, entry: MemoryEntry) -> None
    def query(self, text: str, k: int = 5) -> List[MemoryEntry]
    def clear(self) -> None
    def get_recent(self, limit: int = 10) -> List[MemoryEntry]
    def get_stats(self) -> Dict[str, Any]
```

#### Long-term Memory

```python
class LongTermMemory:
    def __init__(self, persist_path: str)
    def store(self, entry: MemoryEntry) -> None
    def query(self, text: str, k: int = 10) -> List[MemoryEntry]
    def clear(self) -> None
    def get_stats(self) -> Dict[str, Any]
```

#### Memory Entry

```python
@dataclass
class MemoryEntry:
    id: str
    content: str
    metadata: Dict[str, Any]
    timestamp: float
    entry_type: str  # "session" or "persistent"
```

---

### Audio System

#### Enhanced Audio Manager

```python
class EnhancedAudioManager:
    def __init__(self, config: Dict[str, Any])
    def ensure_stt_model(self) -> None
    def get_audio_device_info(self) -> Dict[str, Any]
    def test_audio_input(self, duration: int = 2) -> Dict[str, Any]
    def get_optimal_settings(self) -> Dict[str, Any]
```

#### Audio Input Manager

```python
class AudioInputManager:
    def __init__(self, config: Dict[str, Any])
    def start_recording(self) -> None
    def stop_recording(self) -> bytes
    def is_recording(self) -> bool
    def get_audio_level(self) -> float
```

---

### AI Integration

#### Gemini Client

```python
class GeminiClient:
    def __init__(self, api_key: str, config: Dict[str, Any])
    def generate_text(self, prompt: str) -> str
    def generate_response(self, text: str, context: str = "") -> str
    def is_ready(self) -> bool
    def get_model_info(self) -> Dict[str, Any]
```

#### AI Intent Resolver

```python
class AIIntentResolver:
    def __init__(self, config: Dict[str, Any])
    def resolve_intent(self, text: str, context: str = "") -> Dict[str, Any]
    def generate_command(self, description: str) -> str
    def explain_command(self, command: str) -> str
```

---

## Advanced Features

### Intelligent Cache

#### Class: `IntelligentCache`

```python
class IntelligentCache:
    def __init__(self, config: Dict[str, Any] = None)
    def get(self, key: str, default: Any = None) -> Any
    def set(self, key: str, value: Any, ttl: Optional[float] = None, tags: List[str] = None) -> bool
    def delete(self, key: str) -> bool
    def clear(self, pattern: str = None, tags: List[str] = None) -> int
    def get_stats(self) -> Dict[str, Any]
```

#### Cache Decorator

```python
@cache_result(ttl=300, tags=["weather"])
def expensive_function(param: str) -> str:
    # Function implementation
    pass
```

---

### Dynamic Plugin Loader

#### Class: `DynamicPluginLoader`

```python
class DynamicPluginLoader:
    def __init__(self, config: Dict[str, Any] = None)
    def discover_plugins(self) -> List[PluginMetadata]
    def load_plugin(self, name: str) -> bool
    def unload_plugin(self, name: str) -> bool
    def reload_plugin(self, name: str) -> bool
    def load_all_plugins(self) -> int
    def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]
    def list_plugins_info(self) -> List[Dict[str, Any]]
```

#### Plugin Metadata

```python
@dataclass
class PluginMetadata:
    name: str
    version: str
    description: str
    author: str
    dependencies: List[PluginDependency]
    tags: List[str]
    hot_reloadable: bool
```

---

### Advanced NLP

#### Class: `NLPProcessor`

```python
class NLPProcessor:
    def __init__(self, config: Dict[str, Any] = None)
    def process_text(self, text: str, context: Optional[Context] = None) -> Intent
    def create_context(self, user_id: str, session_id: str) -> Context
    def get_context(self, user_id: str, session_id: str) -> Optional[Context]
    def save_context(self, context: Context) -> None
```

#### Intent and Entities

```python
@dataclass
class Intent:
    type: IntentType
    name: str
    confidence: float
    parameters: Dict[str, Any]
    entities: List[Entity]

@dataclass
class Entity:
    text: str
    type: EntityType
    confidence: float
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any]
```

---

### Task Scheduler

#### Class: `TaskScheduler`

```python
class TaskScheduler:
    def __init__(self, config: Dict[str, Any] = None)
    def add_task(self, task: Task) -> bool
    def remove_task(self, task_id: str) -> bool
    def cancel_task(self, task_id: str) -> bool
    def run_task_now(self, task_id: str) -> bool
    def get_task(self, task_id: str) -> Optional[Task]
    def list_tasks(self, status: Optional[TaskStatus] = None, tags: Optional[List[str]] = None) -> List[Task]
    def get_scheduler_status(self) -> Dict[str, Any]
```

#### Task Definition

```python
@dataclass
class Task:
    id: str
    name: str
    description: str
    function: Callable
    args: tuple
    kwargs: dict
    schedule_type: ScheduleType
    schedule_params: Dict[str, Any]
    priority: TaskPriority
    status: TaskStatus
    max_runs: Optional[int]
    timeout: Optional[float]
    dependencies: List[str]
    tags: List[str]
```

#### Task Decorator

```python
@scheduled_task(ScheduleType.DAILY, {"time": "09:00"})
def daily_backup():
    # Backup implementation
    pass
```

---

### Continuous Learning

#### Class: `ContinuousLearning`

```python
class ContinuousLearning:
    def __init__(self, config: Dict[str, Any] = None)
    def record_interaction(self, context: CommandContext, result: CommandResult, response_time: float, user_id: str = "default") -> None
    def record_user_feedback(self, interaction_id: int, feedback: int, user_id: str = "default") -> None
    def get_user_preferences(self, user_id: str = "default") -> Dict[str, Any]
    def adapt_command_parsing(self, input_text: str, user_id: str = "default") -> Dict[str, Any]
    def suggest_improvements(self) -> List[Dict[str, Any]]
    def learn_new_patterns(self) -> bool
```

#### Learning Data

```python
@dataclass
class LearningData:
    input_text: str
    intent: str
    plugin_used: str
    success: bool
    response_time: float
    user_feedback: Optional[int]
    timestamp: float
    context: Dict[str, Any]
```

---

### Web Interface

#### Class: `WebInterface`

```python
class WebInterface:
    def __init__(self, kernel: Kernel, config: Dict[str, Any] = None)
    async def start_server(self) -> bool
    def stop_server(self) -> None
```

#### API Endpoints

- `GET /api/status` - System status
- `GET /api/plugins` - List plugins
- `POST /api/command` - Execute command
- `GET /api/metrics` - System metrics
- `GET /api/health` - Health check
- `GET /api/learning/preferences` - User preferences
- `POST /api/learning/feedback` - Record feedback
- `GET /api/config` - Configuration
- `GET /api/logs` - Recent logs
- `WS /ws` - WebSocket for real-time updates

---

## Utilities

### Configuration

#### Config Validator

```python
def validate_config(config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]
def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]
def get_default_config() -> Dict[str, Any]
```

### Logging

#### Logger Setup

```python
def setup_logger(name: str, config: Dict[str, Any]) -> logging.Logger
def get_logger(name: str) -> logging.Logger
def set_log_level(level: str) -> None
```

### Exceptions

#### Custom Exceptions

```python
class JarvisException(Exception): pass
class PluginError(JarvisException): pass
class SecurityError(JarvisException): pass
class STTError(JarvisException): pass
class TTSError(JarvisException): pass
class MemoryError(JarvisException): pass
class AudioError(JarvisException): pass
class ValidationError(JarvisException): pass
```

#### Exception Handler Decorator

```python
@handle_exception
def risky_function():
    # Function implementation
    pass
```

### Metrics

#### Success Metrics

```python
class SuccessMetrics:
    def __init__(self, metrics_collector: MetricsCollector)
    def record_command_execution(self, command: str, success: bool, response_time: float, plugin_name: str = None, command_type: str = "text") -> None
    def record_voice_interaction(self, wake_word_detected: bool, transcription_time: float, audio_quality: float = None) -> None
    def record_plugin_performance(self, plugin_name: str, load_time: float, memory_usage: float = None) -> None
    def record_system_resources(self) -> None
    def record_error(self, error_type: str, component: str = None, severity: str = "medium") -> None
    def get_success_report(self, time_window: float = 3600) -> Dict[str, Any]
    def save_success_report(self, filename: str = None) -> str
```

---

## Examples

### Basic Usage

```python
from main import load_config
from core.kernel import Kernel

# Load configuration
config = load_config()

# Initialize kernel
kernel = Kernel(config)

# Execute command
result = kernel.dispatch("echo hello world")
print(result.message)

# Speak text
kernel.speak("Hello, world!")
```

### Plugin Development

```python
from plugins.base_plugin import BasePlugin
from core.interfaces import CommandContext, CommandResult

class CalculatorPlugin(BasePlugin):
    def name(self) -> str:
        return "Calculator"
    
    def patterns(self) -> List[str]:
        return ["calculate", "math", "compute"]
    
    def validate_context(self, ctx: CommandContext) -> bool:
        return any(op in ctx.raw_text for op in ['+', '-', '*', '/'])
    
    def _execute_impl(self, ctx: CommandContext) -> CommandResult:
        try:
            expression = self._extract_expression(ctx.raw_text)
            result = eval(expression)
            
            return CommandResult(
                success=True,
                message=f"Result: {result}",
                data={"expression": expression, "result": result}
            )
        except Exception as e:
            return CommandResult(
                success=False,
                message=f"Calculation error: {e}"
            )
    
    def _extract_expression(self, text: str) -> str:
        # Extract mathematical expression from text
        import re
        match = re.search(r'([\d+\-*/().\s]+)', text)
        return match.group(1).strip() if match else "0"
```

### Security Integration

```python
from core.security import SecurityManager, AutonomyMode

# Initialize security manager
security = SecurityManager(config)

# Set autonomy mode
security.set_autonomy_mode(AutonomyMode.SEMI_AUTO)

# Validate command
from core.interfaces import CommandContext

ctx = CommandContext(
    raw_text="format c:",
    command_name="RunShell",
    params={},
    kernel=None
)

result = security.validate_command(ctx)
if not result.success:
    print(f"Command blocked: {result.message}")
else:
    print("Command allowed")
```

### Memory Usage

```python
from core.memory.short_term import ShortTermMemory
from core.memory.long_term import LongTermMemory
from core.interfaces import MemoryEntry

# Short-term memory
short_memory = ShortTermMemory(max_entries=50)

entry = MemoryEntry(
    id="1",
    content="User asked about weather",
    metadata={"type": "question", "timestamp": time.time()},
    entry_type="session"
)

short_memory.store(entry)

# Query memory
results = short_memory.query("weather", k=3)
for result in results:
    print(result.content)

# Long-term memory
long_memory = LongTermMemory("data/memory")
long_memory.store(entry)
```

### Advanced Features Integration

```python
from core.cache import cache_result, get_cache_instance
from core.task_scheduler import scheduled_task, Task, ScheduleType
from core.continuous_learning import get_continuous_learning

# Cache expensive function
@cache_result(ttl=300, tags=["weather"])
def get_weather(city: str):
    # Expensive API call
    return weather_api.get(city)

# Schedule daily task
@scheduled_task(ScheduleType.DAILY, {"time": "09:00"})
def morning_routine():
    print("Good morning! Starting daily routine...")
    return "Routine completed"

# Record interaction for learning
learning = get_continuous_learning()
learning.record_interaction(context, result, 0.5, "user123")
```

### Web Interface Usage

```python
from core.web_interface import create_web_interface
import asyncio

# Create web interface
web_interface = create_web_interface(kernel, {
    "host": "localhost",
    "port": 8080,
    "enable_cors": True
})

# Start server (async)
async def start_web():
    if web_interface:
        await web_interface.start_server()

# Run the server
asyncio.run(start_web())
```

### Error Handling

```python
from core.exceptions import PluginError, SecurityError, handle_exception

@handle_exception
def risky_operation():
    # This function will have automatic error handling
    pass

try:
    # Custom exception handling
    result = kernel.dispatch("dangerous command")
except SecurityError as e:
    print(f"Security violation: {e}")
except PluginError as e:
    print(f"Plugin error: {e}")
```

---

## Configuration Reference

### Complete Configuration Schema

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

cache:
  memory_limit: 100
  disk_limit: 1000
  default_ttl: 3600
  cleanup_interval: 300

dynamic_plugins:
  plugins_dir: "plugins"
  hot_reload: true

nlp:
  language: "pt-BR"
  confidence_threshold: 0.6

scheduler:
  max_concurrent_tasks: 5
  persistence_file: "data/tasks.json"

learning:
  learning_rate: 0.1
  min_samples: 5
  max_history: 1000

web_interface:
  host: "localhost"
  port: 8080
  enable_cors: true

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

---

## API Best Practices

### 1. Error Handling

Always use proper exception handling:

```python
try:
    result = kernel.dispatch(command)
except SecurityError as e:
    logger.error(f"Security violation: {e}")
    return CommandResult(False, f"Command blocked: {e}")
except PluginError as e:
    logger.error(f"Plugin error: {e}")
    return CommandResult(False, f"Plugin error: {e}")
```

### 2. Resource Management

Use context managers for resources:

```python
with AudioInputManager(config) as audio:
    audio.start_recording()
    # Do something with audio
    data = audio.stop_recording()
```

### 3. Configuration Validation

Always validate configuration:

```python
config, warnings = validate_config(raw_config)
if warnings:
    for warning in warnings:
        logger.warning(f"Configuration warning: {warning}")
```

### 4. Logging

Use structured logging:

```python
logger = get_logger("MyComponent")
logger.info("Operation completed", extra={
    "operation": "test",
    "duration": 1.23,
    "success": True
})
```

### 5. Testing

Write comprehensive tests:

```python
def test_plugin_execution():
    kernel = create_test_kernel()
    result = kernel.dispatch("echo test")
    assert result.success is True
    assert "test" in result.message
```

---

## API Versioning

This API follows semantic versioning. Current version: **v1.0.0**

### Version Compatibility

- **v1.x.x**: Stable API with backward compatibility
- **v2.x.x**: Breaking changes with migration guide
- **v0.x.x**: Development versions (not recommended for production)

### Deprecation Policy

- Deprecated methods will be marked with `@deprecated` decorator
- 6 months notice before removal
- Migration guides provided for breaking changes

---

## Support

For API support and questions:

- **Documentation**: [docs/API.md](API.md)
- **Examples**: [examples/](examples/)
- **Issues**: [GitHub Issues](https://github.com/Bueno135/Jarvis/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Bueno135/Jarvis/discussions)

---

*This API reference is automatically generated from the source code. Last updated: 2026-04-06*
