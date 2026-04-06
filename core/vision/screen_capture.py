from PIL import Image
import io
import logging

logger = logging.getLogger("Jarvis.Vision")

# Lazy import to avoid DISPLAY requirement in headless environments
_pyautogui = None

def _get_pyautogui():
    global _pyautogui
    if _pyautogui is None:
        import pyautogui
        _pyautogui = pyautogui
    return _pyautogui


class ScreenCapture:
    """
    Utility for capturing screen content.
    """
    def __init__(self, config):
        self.config = config

    def capture(self) -> Image.Image:
        """
        Captures the entire primary screen.
        Returns: PIL.Image
        """
        try:
            screenshot = _get_pyautogui().screenshot()
            logger.info("Screenshot taken.")
            return screenshot
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            return None
