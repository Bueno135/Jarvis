"""
Basic usage example for Jarvis.
Demonstrates how to use Jarvis programmatically.
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Basic Jarvis usage example."""
    print("🤖 Jarvis Basic Usage Example")
    print("=" * 40)
    
    # Import Jarvis components
    from main import load_config
    from core.kernel import Kernel
    
    # Load configuration
    print("📋 Loading configuration...")
    config = load_config()
    print(f"✅ App: {config['app']['name']}")
    print(f"✅ Language: {config['app']['language']}")
    
    # Initialize kernel
    print("\n🔧 Initializing kernel...")
    kernel = Kernel(config)
    print("✅ Kernel initialized")
    
    # List available plugins
    print(f"\n🔌 Available plugins: {len(kernel.plugins)}")
    for name, plugin in kernel.plugins.items():
        patterns = ", ".join(plugin.patterns()[:3])  # Show first 3 patterns
        print(f"  - {name}: {patterns}")
    
    # Test some commands
    test_commands = [
        "echo hello world",
        "what time is it",
        "open calculator"
    ]
    
    print(f"\n🧪 Testing {len(test_commands)} commands:")
    for i, command in enumerate(test_commands, 1):
        print(f"\n{i}. Command: {command}")
        result = kernel.dispatch(command)
        print(f"   Result: {result.message}")
        print(f"   Success: {result.success}")
    
    print(f"\n🎉 Example completed successfully!")
    print(f"📊 System state: {kernel.state.value}")

if __name__ == "__main__":
    main()
