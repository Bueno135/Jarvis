"""
Pytest configuration and fixtures for Jarvis testing.
"""
import pytest
import tempfile
import shutil
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    config = {
        "app": {"name": "TestJarvis", "wake_word": "test"},
        "logging": {"level": "DEBUG"},
        "ai": {"enabled": False},
        "stt": {"provider": "whisper"},
        "security": {"autonomy_mode": "manual"},
        "memory": {"max_entries": 10},
        "plugins": {"enabled": []}
    }
    return config

@pytest.fixture
def mock_kernel(mock_config):
    """Mock kernel for tests."""
    from unittest.mock import MagicMock
    from core.kernel import Kernel
    
    # Create a real kernel with mocked dependencies
    with patch('core.kernel.SecurityManager'), \
         patch('core.kernel.PluginLoader'), \
         patch('core.kernel.ShortTermMemory'), \
         patch('core.kernel.LongTermMemory'), \
         patch('core.kernel.EdgeTTSService'):
        
        kernel = Kernel(mock_config)
        kernel.logger = MagicMock()
        return kernel

@pytest.fixture
def mock_command_context():
    """Mock command context for tests."""
    from core.interfaces import CommandContext
    
    return CommandContext(
        raw_text="test command",
        command_name="test",
        params={"param1": "value1"},
        kernel=MagicMock()
    )

@pytest.fixture
def sample_plugins():
    """Sample plugins for testing."""
    from plugins.system.echo import EchoPlugin
    
    return {
        "echo": EchoPlugin()
    }

@pytest.fixture
def mock_audio_data():
    """Mock audio data for testing."""
    import numpy as np
    
    # Generate 1 second of silence at 16kHz
    sample_rate = 16000
    duration = 1.0
    samples = int(sample_rate * duration)
    
    # Generate low amplitude noise
    audio_data = np.random.randint(-100, 100, samples, dtype=np.int16)
    return audio_data.tobytes()

# Test utilities
def create_temp_config_file(config_dict, temp_dir):
    """Create a temporary config file."""
    import yaml
    
    config_path = os.path.join(temp_dir, "config.yaml")
    with open(config_path, 'w') as f:
        yaml.dump(config_dict, f)
    
    return config_path

def assert_command_result(result, success=True, message_contains=None):
    """Assert CommandResult properties."""
    assert result.success == success
    
    if message_contains:
        assert message_contains.lower() in result.message.lower()

def mock_plugin_response(success=True, message="Test response", data=None):
    """Create a mock plugin response."""
    from core.interfaces import CommandResult
    
    return CommandResult(
        success=success,
        message=message,
        data=data or {}
    )

# Markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.audio = pytest.mark.audio
