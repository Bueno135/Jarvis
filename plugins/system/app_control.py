import subprocess
import os
import shlex
from typing import List
from core.interfaces import PluginBase, CommandContext, CommandResult

class OpenAppPlugin(PluginBase):
    def name(self) -> str:
        return "OpenApp"

    def patterns(self) -> List[str]:
        return ["open", "launch", "start"]

    def execute(self, ctx: CommandContext) -> CommandResult:
        # Expected format: "open <app_name>"
        # In a real NLP system, we'd extract the entity.
        # Here we do simple string slicing.
        
        target = ""
        for pattern in self.patterns():
            if ctx.raw_text.startswith(pattern):
                target = ctx.raw_text[len(pattern):].strip()
                break
        
        if not target:
            return CommandResult(False, "Could not identify application name.")

        # Mapping common names to executables (Mock DB)
        app_map = {
            "notepad": "notepad.exe",
            "calc": "calc.exe",
            "calculator": "calc.exe",
            "explorer": "explorer.exe",
            "cmd": "cmd.exe"
        }
        
        executable = app_map.get(target.lower(), target)
        
        try:
            # Security: In a real Scenario, we should verify specific paths.
            # For MVP system built-ins, we use subprocess.Popen
            
            subprocess.Popen(executable, shell=True) # shell=True needed for some system commands
            return CommandResult(True, f"Opened {executable}")
            
        except Exception as e:
            return CommandResult(False, f"Failed to open {target}: {str(e)}")
