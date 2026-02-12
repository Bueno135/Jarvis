import pyautogui
from PIL import Image
import io
from core.logger import setup_logger

class ScreenCapture:
    """
    Utility for capturing screen content.
    """
    def __init__(self, config):
        self.config = config
        self.logger = setup_logger("Jarvis.Vision", config)
        
    def capture(self) -> Image.Image:
        """
        Captures the entire primary screen.
        Returns: PIL.Image
        """
        try:
            screenshot = pyautogui.screenshot()
            self.logger.info("Screenshot taken.")
            return screenshot
        except Exception as e:
            self.logger.error(f"Failed to capture screen: {e}")
            return None
