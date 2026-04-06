#!/usr/bin/env python3
"""
Jarvis Dependency Checker
Verifies and installs all required dependencies for Jarvis.
"""
import sys
import subprocess
import importlib
from pathlib import Path

def check_and_install_dependency(package_name, import_name=None, pip_name=None):
    """Check if a dependency is installed and install it if needed."""
    import_name = import_name or package_name
    pip_name = pip_name or package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name} - Already installed")
        return True
    except ImportError:
        print(f"❌ {package_name} - Not found, installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
            print(f"✅ {package_name} - Successfully installed")
            return True
        except subprocess.CalledProcessError:
            print(f"❌ {package_name} - Failed to install")
            return False

def check_python_version():
    """Check Python version compatibility."""
    version = sys.version_info
    required = (3, 8)
    
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version >= required:
        print(f"✅ Python version compatible (requires {required[0]}.{required[1]}+)")
        return True
    else:
        print(f"❌ Python version too old (requires {required[0]}.{required[1]}+)")
        return False

def check_core_dependencies():
    """Check core Jarvis dependencies."""
    print("\n📦 Checking Core Dependencies:")
    
    core_deps = [
        ("PyYAML", "yaml", "pyyaml"),
        ("Colorlog", "colorlog", "colorlog"),
        ("SoundDevice", "sounddevice", "sounddevice"),
        ("NumPy", "numpy", "numpy"),
        ("Keyboard", "keyboard", "keyboard"),
        ("PyStray", "pystray", "pystray"),
        ("Pillow", "PIL", "Pillow"),
    ]
    
    success_count = 0
    for display_name, import_name, pip_name in core_deps:
        if check_and_install_dependency(display_name, import_name, pip_name):
            success_count += 1
    
    print(f"\nCore dependencies: {success_count}/{len(core_deps)} installed")
    return success_count == len(core_deps)

def check_ai_dependencies():
    """Check AI and ML dependencies."""
    print("\n🤖 Checking AI Dependencies:")
    
    ai_deps = [
        ("Google Generative AI", "google.generativeai", "google-generativeai"),
        ("OpenAI Whisper", "whisper", "openai-whisper"),
        ("Edge TTS", "edge_tts", "edge-tts"),
        ("Transformers", "transformers", "transformers"),
        ("Torch", "torch", "torch"),
    ]
    
    success_count = 0
    for display_name, import_name, pip_name in ai_deps:
        if check_and_install_dependency(display_name, import_name, pip_name):
            success_count += 1
    
    print(f"\nAI dependencies: {success_count}/{len(ai_deps)} installed")
    return success_count >= 3  # At least basic AI features

def check_optional_dependencies():
    """Check optional dependencies for advanced features."""
    print("\n🚀 Checking Optional Dependencies:")
    
    optional_deps = [
        ("ChromaDB", "chromadb", "chromadb"),
        ("Schedule", "schedule", "schedule"),
        ("Watchdog", "watchdog", "watchdog"),
        ("FastAPI", "fastapi", "fastapi"),
        ("Uvicorn", "uvicorn", "uvicorn"),
        ("Psutil", "psutil", "psutil"),
    ]
    
    success_count = 0
    for display_name, import_name, pip_name in optional_deps:
        if check_and_install_dependency(display_name, import_name, pip_name):
            success_count += 1
    
    print(f"\nOptional dependencies: {success_count}/{len(optional_deps)} installed")
    return success_count

def check_system_requirements():
    """Check system-level requirements."""
    print("\n🔧 Checking System Requirements:")
    
    # Check if we're on Windows for specific requirements
    if sys.platform == "win32":
        print("✅ Windows platform detected")
        
        # Check for audio capabilities
        try:
            import sounddevice
            devices = sounddevice.query_devices()
            input_devices = [d for d in devices if d['max_input_channels'] > 0]
            if input_devices:
                print(f"✅ Audio input devices found: {len(input_devices)}")
            else:
                print("⚠️ No audio input devices found - voice commands may not work")
        except ImportError:
            print("⚠️ SoundDevice not available - audio features may not work")
    
    else:
        print(f"✅ {sys.platform} platform detected")
    
    # Check for microphone (basic check)
    try:
        import sounddevice
        default_input = sounddevice.default.device
        if default_input >= 0:
            print("✅ Default audio input device available")
        else:
            print("⚠️ No default audio input device")
    except:
        print("⚠️ Could not check audio devices")

def run_jarvis_test():
    """Test if Jarvis can start successfully."""
    print("\n🧪 Testing Jarvis Startup:")
    
    try:
        # Import main Jarvis components
        from main import load_config
        from core.kernel import Kernel
        
        # Load configuration
        config = load_config()
        print("✅ Configuration loaded successfully")
        
        # Initialize kernel
        kernel = Kernel(config)
        print("✅ Kernel initialized successfully")
        
        # Test a simple command
        result = kernel.dispatch("echo dependency test")
        if result.success:
            print("✅ Command execution test passed")
        else:
            print(f"❌ Command execution test failed: {result.message}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Jarvis startup test failed: {e}")
        return False

def main():
    """Main dependency checker function."""
    print("🔍 Jarvis Dependency Checker")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Python version is not compatible. Please upgrade to Python 3.8 or higher.")
        return False
    
    # Check dependencies
    core_ok = check_core_dependencies()
    ai_ok = check_ai_dependencies()
    optional_ok = check_optional_dependencies()
    
    # Check system requirements
    check_system_requirements()
    
    # Test Jarvis
    jarvis_ok = run_jarvis_test()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DEPENDENCY CHECK SUMMARY")
    print("=" * 50)
    
    print(f"Python Version: ✅ Compatible")
    print(f"Core Dependencies: {'✅ Complete' if core_ok else '❌ Incomplete'}")
    print(f"AI Dependencies: {'✅ Available' if ai_ok else '⚠️ Limited'}")
    print(f"Optional Dependencies: {'✅ Most available' if optional_ok else '⚠️ Basic'}")
    print(f"Jarvis Test: {'✅ Passed' if jarvis_ok else '❌ Failed'}")
    
    if core_ok and jarvis_ok:
        print("\n🎉 Jarvis is ready to use!")
        print("\n📖 Next steps:")
        print("1. Set up GEMINI_API_KEY environment variable for AI features")
        print("2. Run 'python main.py --text \"hello Jarvis\"' to test")
        print("3. Run 'python main.py' to start with voice and UI")
        return True
    else:
        print("\n❌ Jarvis is not ready yet.")
        print("\n🔧 Troubleshooting:")
        if not core_ok:
            print("- Install missing core dependencies manually")
        if not jarvis_ok:
            print("- Check configuration files")
            print("- Verify all components are properly installed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
