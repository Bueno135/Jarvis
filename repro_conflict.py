import sys
import os
print(f"Exec: {sys.executable}")

print("Importing Core Kernel...")
try:
    from core.kernel import Kernel
    print("Core Kernel imported")
except ImportError as e:
    print(f"Failed to import Core Kernel: {e}")

print("Importing Google...")
try:
    import google.genai
    print("Success importing google.genai")
except ImportError as e:
    print(f"Failed to import google.genai: {e}")
