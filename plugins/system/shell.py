import subprocess
import shlex
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
            # shlex.split() para evitar injeção via metacaracteres de shell.
            # shell=False garante que o comando não passe pelo interpretador de shell.
            args = shlex.split(target)
            process = subprocess.run(
                args,
                shell=False,
                capture_output=True,
                text=True,
                timeout=30
            )
            output = process.stdout.strip() or process.stderr.strip()
            return CommandResult(True, f"Executed: {output}")
        except ValueError as e:
            return CommandResult(False, f"Sintaxe inválida no comando: {str(e)}")
        except subprocess.TimeoutExpired:
            return CommandResult(False, "Comando excedeu o tempo limite (30s).")
        except FileNotFoundError:
            return CommandResult(False, f"Comando '{target.split()[0]}' não encontrado no sistema.")
        except Exception as e:
            return CommandResult(False, f"Execution failed: {str(e)}")
