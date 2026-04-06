import logging
from typing import List, Dict, Any
from core.interfaces import PluginBase, CommandContext, CommandResult

logger = logging.getLogger("Jarvis.VisionPlugin")


class VisionPlugin(PluginBase):
    """
    Plugin for screen analysis commands.
    Uses multimodal vision (Gemini) with OCR fallback.
    """

    def __init__(self):
        self._analyzer = None

    def name(self) -> str:
        return "Vision"

    def patterns(self) -> List[str]:
        return [
            "what is on my screen",
            "what do you see",
            "read my screen",
            "o que tem na tela",
            "analise a tela",
            "describe my screen",
            "screen analysis",
            "what's on screen",
        ]

    def intents(self) -> List[str]:
        return ["screen_read", "screen_analyze"]

    def _get_analyzer(self, config):
        if self._analyzer is None:
            from core.vision.analyzer import VisionAnalyzer
            self._analyzer = VisionAnalyzer(config)
        return self._analyzer

    def execute(self, ctx: CommandContext) -> CommandResult:
        """
        Analyze the screen content and speak the result.
        """
        try:
            config = ctx.kernel.config if hasattr(ctx.kernel, 'config') else {}
            analyzer = self._get_analyzer(config)

            # Extract question from params or use default
            question = ctx.params.get("question", ctx.raw_text) if ctx.params else ctx.raw_text
            if not question or question in self.patterns():
                question = "What is currently displayed on this screen? Describe in detail."

            logger.info(f"Analyzing screen with question: {question}")
            analysis = analyzer.analyze_screen(question)

            # Speak the result
            if hasattr(ctx.kernel, 'speak'):
                ctx.kernel.speak(analysis)

            return CommandResult(
                success=True,
                message=analysis,
                data={"analysis": analysis, "question": question}
            )
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            error_msg = f"Failed to analyze screen: {e}"
            if hasattr(ctx.kernel, 'speak'):
                ctx.kernel.speak("Desculpe, não consegui analisar a tela.")
            return CommandResult(success=False, message=error_msg)
