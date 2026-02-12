import sys
import os
print(f"Exec: {sys.executable}")
try:
    import google
    print(f"Google: {google}")
except ImportError:
    print("Failed to import google")

try:
    import google.genai
    print("Success importing google.genai")
except ImportError as e:
    print(f"Failed to import google.genai: {e}")
