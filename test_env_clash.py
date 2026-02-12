import sys
print(f"Testing imports with path: {sys.path}")

try:
    print("Importing vosk...")
    import vosk
    print("Importing sounddevice...")
    import sounddevice
    print("Importing keyboard...")
    import keyboard
    print("Importing pystray...")
    import pystray 
    print("Importing Pillow...")
    from PIL import Image
    
    print("Importing google.genai...")
    import google.genai
    
    print("✅ All imports successful!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
