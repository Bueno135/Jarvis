from typing import List
from core.interfaces import CommandContext, CommandResult
from plugins.base_plugin import BasePlugin

class EchoPlugin(BasePlugin):
    def name(self) -> str:
        return "Echo"

    def patterns(self) -> List[str]:
        return ["echo", "say", "repeat"]

    def validate_context(self, ctx: CommandContext) -> bool:
        """Validate that we have text to echo."""
        return bool(ctx.raw_text and len(ctx.raw_text.strip()) > 0)

    def _execute_impl(self, ctx: CommandContext) -> CommandResult:
        """Implementation of echo functionality."""
        # Extract the actual message to echo (remove command keywords)
        text_to_echo = self._extract_message(ctx.raw_text)
        
        self.log_execution(ctx, CommandResult(True, f"Echo: {text_to_echo}"))
        
        return CommandResult(
            success=True,
            message=f"Echo: {text_to_echo}",
            data={"original_text": ctx.raw_text, "echoed_text": text_to_echo}
        )
    
    def _extract_message(self, raw_text: str) -> str:
        """Extract the actual message from the command text."""
        # Remove command keywords
        keywords = ["echo", "say", "repeat"]
        text = raw_text.lower()
        
        for keyword in keywords:
            if text.startswith(keyword):
                # Remove the keyword and clean up
                result = raw_text[len(keyword):].strip()
                return result if result else "Hello!"
        
        # If no keyword found, return the original text
        return raw_text.strip() if raw_text.strip() else "Hello!"
