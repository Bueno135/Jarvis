from typing import List
from core.interfaces import PluginBase, CommandContext, CommandResult

class EchoPlugin(PluginBase):
    def name(self) -> str:
        return "Echo"

    def patterns(self) -> List[str]:
        return ["echo", "say", "repeat"]

    def execute(self, ctx: CommandContext) -> CommandResult:
        # Simple logic: return the text after the command keyword
        # In a real parser this would be cleaner.
        # For now, just return the whole text or a substring.
        return CommandResult(
            success=True,
            message=f"Echo: {ctx.raw_text}"
        )
