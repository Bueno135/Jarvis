import logging
from typing import Optional, Dict, Any
from PIL import Image

logger = logging.getLogger("Jarvis.Vision.Analyzer")


class VisionAnalyzer:
    """
    Multimodal vision analyzer that captures the screen and sends it
    to a vision-capable LLM for analysis.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._screen_capture = None
        self._gemini_client = None

    def _get_screen_capture(self):
        if self._screen_capture is None:
            from core.vision.screen_capture import ScreenCapture
            self._screen_capture = ScreenCapture(self.config)
        return self._screen_capture

    def _get_gemini(self):
        if self._gemini_client is None:
            from core.ai.gemini_client import GeminiClient
            self._gemini_client = GeminiClient(self.config)
        return self._gemini_client

    def analyze_screen(self, question: str = "What is on this screen?") -> str:
        """
        Capture the screen and analyze it with the multimodal LLM.
        Falls back to OCR if LLM analysis fails.

        Args:
            question: The question to ask about the screen content

        Returns:
            Text description of what's on the screen
        """
        # Capture screenshot
        try:
            screenshot = self._get_screen_capture().capture()
            if screenshot is None:
                return "Failed to capture screen."
        except Exception as e:
            logger.error(f"Screen capture failed: {e}")
            return f"Screen capture error: {e}"

        # Try multimodal LLM analysis
        try:
            gemini = self._get_gemini()
            prompt = f"""Analyze this screenshot and answer the following question.
Respond in a clear, concise way. Answer in the same language as the question.

Question: {question}

Provide your response as JSON: {{"analysis": "your detailed description here"}}"""

            result = gemini.generate_response(prompt, image=screenshot)
            if result and "analysis" in result:
                analysis = result["analysis"]
                logger.info(f"Vision analysis complete: {len(analysis)} chars")
                return analysis
            elif result:
                # Try to extract any text from the result
                return str(result)
        except Exception as e:
            logger.error(f"Multimodal analysis failed: {e}")

        # Fallback to OCR
        logger.info("Falling back to OCR-based analysis")
        return self._fallback_ocr(screenshot)

    def analyze_image(self, image: Image.Image, question: str = "Describe this image.") -> str:
        """Analyze a provided image (not screenshot)."""
        try:
            gemini = self._get_gemini()
            prompt = f"""Analyze this image and answer: {question}
Respond as JSON: {{"analysis": "your answer"}}"""
            result = gemini.generate_response(prompt, image=image)
            if result and "analysis" in result:
                return result["analysis"]
            return str(result) if result else "Analysis failed."
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return self._fallback_ocr(image)

    def _fallback_ocr(self, image: Image.Image) -> str:
        """Fallback to OCR when LLM is unavailable."""
        try:
            from core.vision.ocr import extract_text
            text = extract_text(image)
            if text and not text.startswith("[Image:"):
                return f"OCR text from screen: {text}"
            return "Could not analyze screen content (LLM unavailable, OCR found no text)."
        except Exception as e:
            logger.error(f"OCR fallback failed: {e}")
            return "Screen analysis unavailable."
