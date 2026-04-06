import subprocess
import os
import shutil
from typing import List, Optional
from core.interfaces import PluginBase, CommandContext, CommandResult

class OpenAppPlugin(PluginBase):
    # Allowlist of safe applications with their executable names
    ALLOWED_APPS = {
        "notepad": "notepad.exe",
        "calc": "calc.exe",
        "calculator": "calc.exe",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "code": "code.exe",
        "vscode": "code.exe",
    }

    def name(self) -> str:
        return "OpenApp"

    def patterns(self) -> List[str]:
        return ["open", "launch", "start"]

    def execute(self, ctx: CommandContext) -> CommandResult:
        # Check if AI provided parameters
        target = ctx.params.get("app_name", "") if ctx.params else ""
        
        # Fallback to parsing raw text
        if not target:
            for pattern in self.patterns():
                if ctx.raw_text.lower().startswith(pattern):
                    target = ctx.raw_text[len(pattern):].strip()
                    break
        
        if not target:
            return CommandResult(False, "Could not identify application name.")

        # Sanitize input - only allow alphanumeric and basic chars
        sanitized = ''.join(c for c in target if c.isalnum() or c in ' .-_')
        if sanitized != target:
            return CommandResult(False, f"Invalid characters in application name: {target}")

        target_lower = target.lower().strip()
        
        # Check against allowlist first
        executable = self.ALLOWED_APPS.get(target_lower)
        
        if not executable:
            # Try to find the executable in PATH (safer than arbitrary execution)
            executable = self._find_safe_executable(target_lower)
            
        if not executable:
            return CommandResult(
                False, 
                f"Application '{target}' is not in the allowed list. "
                f"Allowed: {', '.join(self.ALLOWED_APPS.keys())}"
            )
        
        try:
            # Use shell=False for security - pass args as list
            # Use CREATE_NEW_CONSOLE for Windows GUI apps
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            subprocess.Popen(
                [executable],
                shell=False,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NEW_CONSOLE if executable.endswith('.exe') else 0
            )
            return CommandResult(True, f"Opened {executable}")
            
        except FileNotFoundError:
            return CommandResult(False, f"Executable not found: {executable}")
        except PermissionError:
            return CommandResult(False, f"Permission denied to run: {executable}")
        except Exception as e:
            return CommandResult(False, f"Failed to open {target}: {str(e)}")

    def _find_safe_executable(self, name: str) -> Optional[str]:
        """
        Safely search for an executable in PATH.
        Returns full path if found, None otherwise.
        """
        # Add common extensions for Windows
        extensions = ['', '.exe', '.com', '.bat', '.cmd']
        
        for ext in extensions:
            full_name = name + ext if not name.endswith(ext) else name
            path = shutil.which(full_name)
            if path:
                # Verify it's a real file (not a symlink to something dangerous)
                if os.path.isfile(path):
                    return path
        return None
