import subprocess
from typing import List
from core.interfaces import PluginBase, CommandContext, CommandResult

class RunShellPlugin(PluginBase):
    def name(self) -> str:
        return "RunShell"

    def patterns(self) -> List[str]:
        return ["run", "execute"]

    def execute(self, ctx: CommandContext) -> CommandResult:
        # Format: "run <cmd>"
        target = ""
        for pattern in self.patterns():
            if ctx.raw_text.startswith(pattern):
                target = ctx.raw_text[len(pattern):].strip()
                break

        if not target:
            return CommandResult(False, "No command provided.")

        # SECURITY CHECK
        security = ctx.kernel.get_service("security")
        if not security:
            return CommandResult(False, "Security service unavailable.")

        if not security.can_execute_shell(target):
            return CommandResult(False, f"Command '{target}' is BLOCKED by whitelist.")

        try:
            # capture_output=True to return the result
            process = subprocess.run(target, shell=True, capture_output=True, text=True)
            output = process.stdout.strip() or process.stderr.strip()
            return CommandResult(True, f"Executed: {output}")
        except Exception as e:
            return CommandResult(False, f"Execution failed: {str(e)}")
