# Jarvis Development Guide

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Plugin Development](#plugin-development)
- [Testing](#testing)
- [Debugging](#debugging)
- [Performance Optimization](#performance-optimization)
- [Security Guidelines](#security-guidelines)
- [Documentation](#documentation)
- [Release Process](#release-process)

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Code editor (VS Code recommended)
- Basic understanding of Python and asynchronous programming

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Bueno135/Jarvis.git
   cd Jarvis
   ```

2. **Create virtual environment**
   ```bash
   python -m venv dev-env
   
   # Windows
   dev-env\Scripts\activate
   
   # Linux/Mac
   source dev-env/bin/activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If exists
   ```

4. **Verify setup**
   ```bash
   python scripts/verify_system.py
   python -m pytest tests/
   ```

### Recommended VS Code Extensions

- Python
- Pylance
- Python Docstring Generator
- GitLens
- Bracket Pair Colorizer
- Indent-Rainbow
- Thunder Client (for API testing)

---

## Development Environment

### Environment Configuration

Create a `.env.development` file:

```bash
# Development settings
DEBUG=true
LOG_LEVEL=DEBUG
JARVIS_LOG_LEVEL=DEBUG

# API Keys (for development)
GEMINI_API_KEY=your_development_key

# Development database
MEMORY_PATH=dev_data/memory
CACHE_PATH=dev_data/cache
LOGS_PATH=dev_data/logs
```

### Development Scripts

Create useful development scripts in `scripts/dev/`:

#### `scripts/dev/run_tests.sh`
```bash
#!/bin/bash
echo "Running all tests..."
python -m pytest tests/ -v --cov=core --cov-report=html
echo "Test coverage report generated in htmlcov/"
```

#### `scripts/dev/run_lint.sh`
```bash
#!/bin/bash
echo "Running linting..."
flake8 core/ plugins/ ui/ --max-line-length=88 --extend-ignore=E203
black --check core/ plugins/ ui/
mypy core/ --ignore-missing-imports
```

#### `scripts/dev/run_security.sh`
```bash
#!/bin/bash
echo "Running security checks..."
bandit -r core/ plugins/ ui/
safety check
```

---

## Project Structure

### Core Architecture

```
jarvis/
├── core/                    # Core system components
│   ├── kernel.py           # Main orchestrator
│   ├── interfaces.py       # Abstract interfaces
│   ├── security.py         # Security management
│   ├── plugin_loader.py    # Plugin system
│   ├── memory/             # Memory management
│   ├── stt/               # Speech-to-text
│   ├── tts/               # Text-to-speech
│   ├── ai/                # AI integration
│   └── exceptions.py       # Custom exceptions
├── plugins/                # Plugin ecosystem
│   ├── base_plugin.py     # Plugin base class
│   ├── system/            # System plugins
│   └── web/               # Web plugins
├── ui/                     # User interface
│   ├── ui_manager.py      # UI coordinator
│   ├── tray.py            # System tray
│   └── overlay.py         # Visual overlay
├── tests/                  # Test suite
├── docs/                   # Documentation
├── scripts/                # Utility scripts
└── examples/               # Usage examples
```

### Component Responsibilities

- **Kernel**: Central orchestrator, plugin management, command dispatch
- **Security**: Command validation, autonomy modes, whitelist management
- **Plugin Loader**: Dynamic plugin discovery and loading
- **Memory**: Short-term and long-term memory management
- **STT/TTS**: Audio processing and speech synthesis
- **AI**: Natural language processing and intent resolution

---

## Coding Standards

### Python Style Guide

Follow [PEP 8](https://pep8.org/) with these modifications:

- **Line length**: 88 characters (Black default)
- **String quotes**: Single quotes for strings, double quotes for docstrings
- **Import order**: Standard library, third-party, local imports
- **Type hints**: Required for all public functions and methods

### Code Formatting

Use [Black](https://black.readthedocs.io/) for code formatting:

```bash
pip install black
black --line-length 88 .
```

### Type Hints

```python
from typing import Dict, List, Optional, Union, Callable, Any

def process_command(
    text: str, 
    context: Optional[CommandContext] = None
) -> CommandResult:
    """Process a command with optional context."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def execute_command(self, ctx: CommandContext) -> CommandResult:
    """Execute a command with the given context.
    
    Args:
        ctx: Command context containing the command details
        
    Returns:
        CommandResult with the execution result
        
    Raises:
        ValidationError: If the context is invalid
        SecurityError: If the command is not allowed
    """
    pass
```

### Error Handling

Use specific exception types:

```python
from core.exceptions import PluginError, SecurityError

def safe_execute(self, ctx: CommandContext) -> CommandResult:
    try:
        return self._execute_impl(ctx)
    except SecurityError as e:
        self.logger.error(f"Security violation: {e}")
        return CommandResult(False, f"Command blocked: {e}")
    except Exception as e:
        self.logger.error(f"Unexpected error: {e}", exc_info=True)
        return CommandResult(False, f"Error: {e}")
```

---

## Plugin Development

### Plugin Template

Use the plugin template generator:

```bash
python scripts/create_plugin.py MyPlugin system
```

### Plugin Structure

```
plugins/category/my_plugin.py
```

```python
from plugins.base_plugin import BasePlugin
from core.interfaces import CommandContext, CommandResult
from typing import List

class MyPlugin(BasePlugin):
    """Description of what this plugin does."""
    
    __version__ = "1.0.0"
    __author__ = "Your Name"
    __description__ = "A brief description"
    __tags__ = ["category", "functionality"]
    __dependencies__ = []
    __hot_reloadable__ = True
    
    def name(self) -> str:
        return "MyPlugin"
    
    def patterns(self) -> List[str]:
        return [
            "mycommand",
            "do something",
            "execute myfunction"
        ]
    
    def validate_context(self, ctx: CommandContext) -> bool:
        """Validate command before execution."""
        return bool(ctx.raw_text.strip())
    
    def _execute_impl(self, ctx: CommandContext) -> CommandResult:
        """Main plugin implementation."""
        try:
            # Your implementation here
            result = self._do_something(ctx.params)
            
            self.log_execution(ctx, CommandResult(True, "Success!"))
            
            return CommandResult(
                success=True,
                message=f"MyPlugin executed: {result}",
                data={"result": result}
            )
            
        except Exception as e:
            self.logger.error(f"Execution failed: {e}")
            return CommandResult(False, f"Error: {e}")
    
    def _do_something(self, params: Dict[str, Any]) -> Any:
        """Your custom logic."""
        return "Done!"
    
    def get_help(self) -> str:
        """Return help text for this plugin."""
        return """
        MyPlugin Help:
        - mycommand: Execute my function
        - do something: Perform an action
        - execute myfunction: Run my function
        
        Examples:
        - "mycommand with parameter"
        - "do something now"
        """
```

### Plugin Best Practices

1. **Validation**: Always validate input in `validate_context()`
2. **Error Handling**: Use specific exceptions and proper logging
3. **Documentation**: Provide clear docstrings and help text
4. **Testing**: Write comprehensive tests for your plugin
5. **Performance**: Use caching for expensive operations

### Plugin Testing

Create `tests/test_my_plugin.py`:

```python
import pytest
from plugins.category.my_plugin import MyPlugin
from core.interfaces import CommandContext, CommandResult

class TestMyPlugin:
    def setup_method(self):
        self.plugin = MyPlugin()
    
    def test_name(self):
        assert self.plugin.name() == "MyPlugin"
    
    def test_patterns(self):
        patterns = self.plugin.patterns()
        assert "mycommand" in patterns
    
    def test_validate_context_valid(self):
        ctx = CommandContext(
            raw_text="mycommand test",
            command_name="MyPlugin",
            params={},
            kernel=None
        )
        assert self.plugin.validate_context(ctx) is True
    
    def test_validate_context_invalid(self):
        ctx = CommandContext(
            raw_text="",
            command_name="MyPlugin",
            params={},
            kernel=None
        )
        assert self.plugin.validate_context(ctx) is False
    
    def test_execute_success(self):
        ctx = CommandContext(
            raw_text="mycommand test",
            command_name="MyPlugin",
            params={"test": "value"},
            kernel=None
        )
        
        result = self.plugin.execute(ctx)
        assert result.success is True
        assert "MyPlugin executed" in result.message
    
    def test_execute_failure(self):
        ctx = CommandContext(
            raw_text="mycommand",
            command_name="MyPlugin",
            params={},
            kernel=None
        )
        
        # Mock failure
        with unittest.mock.patch.object(self.plugin, '_do_something', side_effect=Exception("Test error")):
            result = self.plugin.execute(ctx)
            assert result.success is False
            assert "Error:" in result.message
```

---

## Testing

### Test Structure

```
tests/
├── conftest.py              # Pytest configuration
├── unit/                    # Unit tests
│   ├── test_kernel.py
│   ├── test_security.py
│   └── test_plugins.py
├── integration/             # Integration tests
│   ├── test_command_flow.py
│   └── test_audio_pipeline.py
├── e2e/                     # End-to-end tests
│   └── test_full_workflow.py
└── fixtures/                # Test fixtures
    ├── sample_config.yaml
    └── mock_plugins.py
```

### Test Configuration

`conftest.py`:

```python
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    return {
        "app": {"name": "TestJarvis", "language": "pt-BR"},
        "logging": {"level": "DEBUG"},
        "security": {"autonomy_mode": "manual"},
        "ai": {"enabled": False},
        "stt": {"provider": "whisper"},
        "memory": {"max_entries": 10}
    }

@pytest.fixture
def mock_kernel(mock_config):
    """Mock kernel for tests."""
    with unittest.mock.patch('core.kernel.SecurityManager'), \
         unittest.mock.patch('core.kernel.PluginLoader'), \
         unittest.mock.patch('core.kernel.ShortTermMemory'):
        from core.kernel import Kernel
        return Kernel(mock_config)
```

### Running Tests

```bash
# All tests
python -m pytest tests/

# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# With coverage
python -m pytest --cov=core --cov-report=html

# Specific test file
python -m pytest tests/unit/test_kernel.py -v

# With markers
python -m pytest -m "unit and not slow"
```

### Test Markers

```python
import pytest

@pytest.mark.unit
def test_unit_example():
    pass

@pytest.mark.integration
def test_integration_example():
    pass

@pytest.mark.slow
def test_slow_example():
    pass

@pytest.mark.web
def test_web_example():
    pass
```

### Test Best Practices

1. **Isolation**: Tests should not depend on each other
2. **Mocking**: Use mocks for external dependencies
3. **Fixtures**: Use fixtures for common setup
4. **Assertions**: Be specific with assertions
5. **Coverage**: Aim for >80% code coverage

---

## Debugging

### Logging Configuration

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use Jarvis logger
from core.logger import get_logger
logger = get_logger("Debug")
logger.setLevel(logging.DEBUG)
```

### Debug Tools

#### Memory Profiling

```python
import tracemalloc

tracemalloc.start()
# Your code here
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

#### Performance Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# Your code here
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

#### Debug Decorator

```python
from functools import wraps
import time
import logging

def debug_timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logging.debug(f"{func.__name__} took {end - start:.3f}s")
        return result
    return wrapper

@debug_timer
def my_function():
    time.sleep(0.1)
    return "done"
```

### Common Debugging Scenarios

#### Plugin Not Loading

```python
# Check plugin registration
from core.plugin_loader import PluginLoader

loader = PluginLoader()
plugins = loader.discover_and_load()
print(f"Loaded plugins: {[p.name() for p in plugins]}")

# Check specific plugin
try:
    from plugins.system.echo import EchoPlugin
    plugin = EchoPlugin()
    print(f"Plugin patterns: {plugin.patterns()}")
except ImportError as e:
    print(f"Import error: {e}")
```

#### Command Not Recognized

```python
# Check plugin patterns
kernel = Kernel(config)
for name, plugin in kernel.plugins.items():
    print(f"{name}: {plugin.patterns()}")

# Test pattern matching
import re
text = "echo hello world"
for name, plugin in kernel.plugins.items():
    for pattern in plugin.patterns():
        if re.search(pattern, text, re.IGNORECASE):
            print(f"Match: {name} with pattern '{pattern}'")
```

#### Audio Issues

```python
# Test audio devices
import sounddevice as sd
devices = sd.query_devices()
print("Available devices:")
for i, device in enumerate(devices):
    print(f"{i}: {device['name']} (inputs: {device['max_input_channels']})")

# Test audio recording
from core.enhanced_audio import EnhancedAudioManager
audio = EnhancedAudioManager(config)
result = audio.test_audio_input(duration=2)
print(f"Audio test result: {result}")
```

---

## Performance Optimization

### Profiling Guidelines

1. **Identify bottlenecks** before optimizing
2. **Measure before and after** changes
3. **Focus on hot paths** (frequently called code)
4. **Consider algorithmic improvements** before micro-optimizations

### Optimization Techniques

#### Caching

```python
from core.cache import cache_result

@cache_result(ttl=300, tags=["expensive"])
def expensive_computation(data):
    # Expensive computation
    return result
```

#### Lazy Loading

```python
class LazyResource:
    def __init__(self):
        self._resource = None
    
    @property
    def resource(self):
        if self._resource is None:
            self._resource = self._load_resource()
        return self._resource
    
    def _load_resource(self):
        # Expensive resource loading
        pass
```

#### Batch Processing

```python
def process_items_batch(items, batch_size=100):
    """Process items in batches to reduce memory usage."""
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        yield process_batch(batch)
```

#### Memory Management

```python
import gc
import weakref

# Use weak references for caches
cache = weakref.WeakValueDictionary()

# Explicit garbage collection
def cleanup():
    gc.collect()
```

### Performance Monitoring

```python
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        
        # Log slow functions
        if duration > 1.0:
            logging.warning(f"Slow function {func.__name__}: {duration:.3f}s")
        
        return result
    return wrapper
```

---

## Security Guidelines

### Security Best Practices

1. **Input Validation**: Always validate user input
2. **Principle of Least Privilege**: Minimize permissions
3. **Secure Defaults**: Default to secure configurations
4. **Audit Logging**: Log security-relevant events
5. **Regular Updates**: Keep dependencies updated

### Command Validation

```python
from core.security import SecurityManager

def validate_command(command: str, context: Dict[str, Any]) -> bool:
    security = SecurityManager(config)
    
    # Check against dangerous patterns
    dangerous_patterns = [
        r'rm\s+-rf\s+/',
        r'format\s+[a-z]:',
        r'del\s+/s',
        r'sudo\s+rm',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return False
    
    return True
```

### Data Protection

```python
import hashlib
import secrets

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for storage."""
    return hashlib.sha256(data.encode()).hexdigest()

def generate_secure_token() -> str:
    """Generate cryptographically secure token."""
    return secrets.token_urlsafe(32)
```

### API Security

```python
from functools import wraps

def require_authentication(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Check authentication
        if not is_authenticated():
            raise SecurityError("Authentication required")
        return func(*args, **kwargs)
    return wrapper

def rate_limit(max_calls: int, time_window: int):
    """Rate limiting decorator."""
    calls = []
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            calls[:] = [call for call in calls if now - call < time_window]
            
            if len(calls) >= max_calls:
                raise SecurityError("Rate limit exceeded")
            
            calls.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## Documentation

### Documentation Standards

1. **API Documentation**: Keep API docs updated
2. **Code Comments**: Explain complex logic
3. **README**: Clear setup and usage instructions
4. **Changelog**: Document all changes
5. **Architecture Docs**: Explain design decisions

### Documentation Tools

- **Sphinx**: For API documentation
- **MkDocs**: For static sites
- **Swagger/OpenAPI**: For REST APIs
- **Diagrams**: Use Mermaid for architecture diagrams

### Example Documentation

```python
def complex_algorithm(data: List[str]) -> Dict[str, int]:
    """
    Process a list of strings and return word frequency.
    
    This function implements the following algorithm:
    1. Normalize all strings to lowercase
    2. Split strings into words
    3. Count word frequencies
    4. Return sorted dictionary
    
    Args:
        data: List of strings to process
        
    Returns:
        Dictionary with word frequencies, sorted by count
        
    Example:
        >>> complex_algorithm(["Hello world", "Hello Python"])
        {'hello': 2, 'world': 1, 'python': 1}
        
    Raises:
        ValueError: If data is empty or contains non-strings
    """
    pass
```

---

## Release Process

### Version Management

Use semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Checklist

1. **Code Quality**
   - [ ] All tests pass
   - [ ] Code coverage >80%
   - [ ] No linting errors
   - [ ] Security scan passes

2. **Documentation**
   - [ ] API docs updated
   - [ ] CHANGELOG updated
   - [ ] README updated
   - [ ] Examples tested

3. **Testing**
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Manual testing completed
   - [ ] Performance benchmarks run

4. **Build**
   - [ ] Build package
   - [ ] Test installation
   - [ ] Verify functionality

### Release Script

`scripts/release.py`:

```python
#!/usr/bin/env python3
"""Release automation script."""

import subprocess
import sys
from pathlib import Path

def run_command(cmd: str) -> bool:
    """Run command and return success status."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True

def main():
    """Main release process."""
    version = sys.argv[1] if len(sys.argv) > 1 else input("Version: ")
    
    print(f"Releasing Jarvis v{version}")
    
    # Run tests
    if not run_command("python -m pytest tests/"):
        print("Tests failed!")
        return 1
    
    # Run linting
    if not run_command("flake8 core/ plugins/ ui/"):
        print("Linting failed!")
        return 1
    
    # Build documentation
    if not run_command("mkdocs build"):
        print("Documentation build failed!")
        return 1
    
    # Update version
    with open("VERSION", "w") as f:
        f.write(version)
    
    # Tag release
    if not run_command(f"git tag -a v{version} -m 'Release v{version}'"):
        print("Git tagging failed!")
        return 1
    
    print(f"Release v{version} completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Continuous Integration

`.github/workflows/ci.yml`:

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov flake8 black
    
    - name: Run tests
      run: |
        python -m pytest tests/ --cov=core --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
    
    - name: Lint
      run: |
        flake8 core/ plugins/ ui/
        black --check core/ plugins/ ui/
```

---

## Contributing

### Contribution Workflow

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Update documentation
6. Submit pull request

### Code Review Guidelines

- **Functionality**: Does it work as intended?
- **Code Quality**: Is it well-written and maintainable?
- **Testing**: Are tests comprehensive?
- **Documentation**: Is it properly documented?
- **Performance**: Any performance implications?

### Community Guidelines

- Be respectful and constructive
- Help newcomers get started
- Share knowledge and experience
- Follow the code of conduct

---

*This development guide is continuously updated. Last updated: 2026-04-06*
