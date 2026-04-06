#!/usr/bin/env python3
"""
Jarvis System Verification Script
Checks all dependencies and components for proper functionality.
"""
import sys
import os
import importlib
import subprocess
from pathlib import Path

def print_header():
    """Print verification header."""
    print("🔍 Jarvis System Verification")
    print("=" * 50)

def check_python_version():
    """Check Python version compatibility."""
    version = sys.version_info
    required = (3, 8)
    
    print(f"📦 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version >= required:
        print("✅ Python version compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} (requires {required[0]}.{required[1]}+)")
        return False

def check_dependencies():
    """Check if all required dependencies are installed."""
    required = [
        'yaml', 'colorlog', 'sounddevice', 'numpy', 
        'keyboard', 'pystray', 'Pillow', 'google-genai'
    ]
    
    print("\n📦 Checking Dependencies:")
    
    missing = []
    for dep in required:
        try:
            importlib.import_module(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}")
            missing.append(dep)
    
    return len(missing) == 0, missing

def check_core_modules():
    """Check if all core modules exist and can be imported."""
    core_modules = [
        "core.kernel", "core.config_validator", "core.logger",
        "core.security", "core.plugin_loader", "core.task_planner",
        "core.exceptions", "core.enhanced_audio", "core.integrity_checker"
    ]
    
    print("\n🧩 Checking Core Modules:")
    
    missing = []
    for module in core_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            missing.append(module)
    
    return len(missing) == 0, missing

def check_config_files():
    """Check configuration files."""
    config_files = [
        "config/config.yaml",
        "config/whitelist.yaml"
    ]
    
    print("\n⚙️ Checking Configuration Files:")
    
    missing = []
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {config_file}")
        else:
            print(f"❌ {config_file}")
            missing.append(config_file)
    
    return len(missing) == 0, missing

def check_plugins():
    """Check plugin system."""
    plugins_dir = Path("plugins")
    
    print("\n🔌 Checking Plugin System:")
    
    if not plugins_dir.exists():
        print("❌ Plugins directory not found")
        return False, ["plugins directory"]
    
    # Count plugin files
    plugin_files = list(plugins_dir.rglob("*.py"))
    plugin_files = [f for f in plugin_files if not f.name.startswith("__")]
    
    print(f"📁 Found {len(plugin_files)} plugin files")
    
    try:
        from core.plugin_loader import PluginLoader
        loader = PluginLoader()
        loaded_plugins = loader.discover_and_load()
        
        print(f"✅ Loaded {len(loaded_plugins)} plugins")
        for plugin in loaded_plugins:
            print(f"   - {plugin.name()}")
        
        return True, []
    except Exception as e:
        print(f"❌ Plugin loading failed: {e}")
        return False, [str(e)]

def check_audio_system():
    """Check audio system components."""
    audio_components = {
        "sounddevice": "Audio input/output",
        "numpy": "Audio processing",
        "whisper": "Speech recognition",
        "edge_tts": "Text-to-speech"
    }
    
    print("\n🎤 Checking Audio System:")
    
    available = []
    missing = []
    
    for component, description in audio_components.items():
        try:
            importlib.import_module(component)
            print(f"✅ {component} ({description})")
            available.append(component)
        except ImportError:
            print(f"❌ {component} ({description})")
            missing.append(component)
    
    return len(available) >= 2, missing  # At least basic audio

def check_ui_components():
    """Check UI components."""
    ui_components = {
        "tkinter": "Overlay UI",
        "pystray": "System Tray",
        "PIL": "Image processing"
    }
    
    print("\n🖥️ Checking UI Components:")
    
    available = []
    missing = []
    
    for component, description in ui_components.items():
        try:
            importlib.import_module(component)
            print(f"✅ {component} ({description})")
            available.append(component)
        except ImportError:
            print(f"❌ {component} ({description})")
            missing.append(component)
    
    return len(available) > 0, missing

def check_memory_system():
    """Check memory system."""
    print("\n💾 Checking Memory System:")
    
    try:
        from core.memory.short_term import ShortTermMemory
        print("✅ Short-term memory available")
        
        try:
            from core.memory.long_term import LongTermMemory
            print("✅ Long-term memory available")
            return True, []
        except ImportError:
            print("⚠️ Long-term memory missing (chromadb)")
            return True, ["chromadb"]
            
    except ImportError as e:
        print(f"❌ Memory system unavailable: {e}")
        return False, [str(e)]

def check_security():
    """Check security components."""
    print("\n🛡️ Checking Security System:")
    
    try:
        from core.security import SecurityManager
        
        # Check whitelist file
        if os.path.exists("config/whitelist.yaml"):
            print("✅ Security manager and whitelist available")
        else:
            print("⚠️ Security manager OK, no whitelist file")
        
        return True, []
    except Exception as e:
        print(f"❌ Security system error: {e}")
        return False, [str(e)]

def run_basic_test():
    """Run a basic functionality test."""
    print("\n🧪 Running Basic Test:")
    
    try:
        from main import load_config
        from core.kernel import Kernel
        
        # Load config
        config = load_config()
        print("✅ Configuration loaded")
        
        # Test with mocked dependencies
        import unittest.mock as mock
        
        with mock.patch('core.kernel.SecurityManager'), \
             mock.patch('core.kernel.PluginLoader'), \
             mock.patch('core.kernel.ShortTermMemory'), \
             mock.patch('core.kernel.LongTermMemory'), \
             mock.patch('core.kernel.EdgeTTSService'):
            
            kernel = Kernel(config)
            print("✅ Kernel initialized")
            
            # Test echo command
            result = kernel.dispatch("echo test")
            if result.success:
                print("✅ Basic command execution works")
                return True, []
            else:
                print(f"❌ Command execution failed: {result.message}")
                return False, [result.message]
                
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False, [str(e)]

def main():
    """Main verification function."""
    print_header()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", lambda: check_dependencies()[0]),
        ("Core Modules", lambda: check_core_modules()[0]),
        ("Configuration", lambda: check_config_files()[0]),
        ("Plugins", lambda: check_plugins()[0]),
        ("Audio System", lambda: check_audio_system()[0]),
        ("UI Components", lambda: check_ui_components()[0]),
        ("Memory System", lambda: check_memory_system()[0]),
        ("Security", lambda: check_security()[0]),
        ("Basic Test", lambda: run_basic_test()[0])
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check failed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\nResults: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Jarvis is ready to run.")
        return 0
    elif passed >= total * 0.8:  # 80% or more
        print("⚠️ Most checks passed. Jarvis should work with some limitations.")
        return 0
    else:
        print("❌ Critical issues found. Please fix before running Jarvis.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
