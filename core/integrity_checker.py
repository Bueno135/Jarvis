"""
System integrity checker for Jarvis.
Validates system components, dependencies, and configuration.
"""
import os
import sys
import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class Status(Enum):
    OK = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    INFO = "ℹ️"

@dataclass
class CheckResult:
    """Result of a system check."""
    component: str
    status: Status
    message: str
    details: Dict[str, Any] = None

class SystemIntegrityChecker:
    """Comprehensive system integrity checker."""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.results: List[CheckResult] = []
        
    def run_all_checks(self) -> List[CheckResult]:
        """Run all integrity checks."""
        self.results = []
        
        print("🔍 Running Jarvis System Integrity Check...")
        print("=" * 50)
        
        # Core checks
        self.check_python_version()
        self.check_dependencies()
        self.check_core_modules()
        self.check_configuration()
        self.check_plugins()
        self.check_memory_system()
        self.check_audio_system()
        self.check_ui_components()
        self.check_security()
        
        # Generate summary
        self.print_summary()
        
        return self.results
    
    def check_python_version(self):
        """Check Python version compatibility."""
        version = sys.version_info
        required = (3, 8)
        
        if version >= required:
            self.results.append(CheckResult(
                "Python Version",
                Status.OK,
                f"Python {version.major}.{version.minor}.{version.micro}",
                {"version": f"{version.major}.{version.minor}.{version.micro}", "required": f"{required[0]}.{required[1]}"}
            ))
        else:
            self.results.append(CheckResult(
                "Python Version",
                Status.ERROR,
                f"Python {version.major}.{version.minor} (requires {required[0]}.{required[1]}+)",
                {"current": f"{version.major}.{version.minor}", "required": f"{required[0]}.{required[1]}+"}
            ))
    
    def check_dependencies(self):
        """Check required dependencies."""
        required_packages = [
            'yaml', 'colorlog', 'sounddevice', 'numpy', 
            'keyboard', 'pystray', 'Pillow', 'google-genai'
        ]
        
        missing = []
        for package in required_packages:
            try:
                importlib.import_module(package)
            except ImportError:
                missing.append(package)
        
        if not missing:
            self.results.append(CheckResult(
                "Dependencies",
                Status.OK,
                f"All {len(required_packages)} required packages installed"
            ))
        else:
            self.results.append(CheckResult(
                "Dependencies",
                Status.ERROR,
                f"Missing {len(missing)} packages: {', '.join(missing)}",
                {"missing": missing, "total": len(required_packages)}
            ))
    
    def check_core_modules(self):
        """Check core module availability."""
        core_modules = [
            "core.kernel", "core.config_validator", "core.logger",
            "core.security", "core.plugin_loader", "core.task_planner",
            "core.exceptions", "core.enhanced_audio"
        ]
        
        missing = []
        for module in core_modules:
            try:
                importlib.import_module(module)
            except ImportError as e:
                missing.append(f"{module}: {e}")
        
        if not missing:
            self.results.append(CheckResult(
                "Core Modules",
                Status.OK,
                f"All {len(core_modules)} core modules available"
            ))
        else:
            self.results.append(CheckResult(
                "Core Modules",
                Status.ERROR,
                f"Missing {len(missing)} modules",
                {"missing": missing}
            ))
    
    def check_configuration(self):
        """Check configuration files."""
        config_files = [
            "config/config.yaml",
            "config/whitelist.yaml"
        ]
        
        missing = []
        for config_file in config_files:
            if not (self.project_root / config_file).exists():
                missing.append(config_file)
        
        if not missing:
            # Try to load and validate config
            try:
                from main import load_config
                config = load_config()
                
                self.results.append(CheckResult(
                    "Configuration",
                    Status.OK,
                    "Configuration files present and valid"
                ))
            except Exception as e:
                self.results.append(CheckResult(
                    "Configuration",
                    Status.ERROR,
                    f"Configuration error: {e}",
                    {"error": str(e)}
                ))
        else:
            self.results.append(CheckResult(
                "Configuration",
                Status.ERROR,
                f"Missing config files: {', '.join(missing)}",
                {"missing": missing}
            ))
    
    def check_plugins(self):
        """Check plugin system."""
        plugins_dir = self.project_root / "plugins"
        
        if not plugins_dir.exists():
            self.results.append(CheckResult(
                "Plugins",
                Status.ERROR,
                "Plugins directory not found"
            ))
            return
        
        # Count plugin files
        plugin_files = list(plugins_dir.rglob("*.py"))
        plugin_files = [f for f in plugin_files if not f.name.startswith("__")]
        
        if plugin_files:
            try:
                from core.plugin_loader import PluginLoader
                loader = PluginLoader()
                loaded_plugins = loader.discover_and_load()
                
                self.results.append(CheckResult(
                    "Plugins",
                    Status.OK,
                    f"Found {len(plugin_files)} plugin files, loaded {len(loaded_plugins)} plugins",
                    {"files_found": len(plugin_files), "plugins_loaded": len(loaded_plugins)}
                ))
            except Exception as e:
                self.results.append(CheckResult(
                    "Plugins",
                    Status.WARNING,
                    f"Plugin files found but loading failed: {e}",
                    {"files_found": len(plugin_files), "error": str(e)}
                ))
        else:
            self.results.append(CheckResult(
                "Plugins",
                Status.WARNING,
                "No plugin files found"
            ))
    
    def check_memory_system(self):
        """Check memory system components."""
        try:
            from core.memory.short_term import ShortTermMemory
            from core.memory.long_term import LongTermMemory
            
            # Test short-term memory
            stm = ShortTermMemory(max_entries=5)
            
            # Test long-term memory (might fail due to missing chromadb)
            try:
                ltm = LongTermMemory("/tmp/test_memory")
                ltm_status = Status.OK
                ltm_msg = "Both memory systems available"
            except ImportError:
                ltm_status = Status.WARNING
                ltm_msg = "Short-term memory OK, long-term memory missing chromadb"
            
            self.results.append(CheckResult(
                "Memory System",
                ltm_status,
                ltm_msg
            ))
            
        except ImportError as e:
            self.results.append(CheckResult(
                "Memory System",
                Status.ERROR,
                f"Memory system unavailable: {e}"
            ))
    
    def check_audio_system(self):
        """Check audio system components."""
        audio_components = {
            "sounddevice": "Audio input/output",
            "numpy": "Audio processing",
            "whisper": "Speech recognition",
            "edge_tts": "Text-to-speech"
        }
        
        available = {}
        missing = []
        
        for component, description in audio_components.items():
            try:
                importlib.import_module(component)
                available[component] = description
            except ImportError:
                missing.append(f"{component} ({description})")
        
        if len(available) >= 2:  # At least basic audio
            status = Status.OK if not missing else Status.WARNING
            message = f"Audio components available: {', '.join(available.keys())}"
            if missing:
                message += f" (Missing: {', '.join(missing)})"
                
            self.results.append(CheckResult(
                "Audio System",
                status,
                message,
                {"available": available, "missing": missing}
            ))
        else:
            self.results.append(CheckResult(
                "Audio System",
                Status.ERROR,
                f"Insufficient audio components. Missing: {', '.join(missing)}",
                {"missing": missing}
            ))
    
    def check_ui_components(self):
        """Check UI components."""
        ui_components = {
            "tkinter": "Overlay UI",
            "pystray": "System Tray",
            "PIL": "Image processing"
        }
        
        available = {}
        missing = []
        
        for component, description in ui_components.items():
            try:
                importlib.import_module(component)
                available[component] = description
            except ImportError:
                missing.append(f"{component} ({description})")
        
        if available:
            status = Status.OK if not missing else Status.WARNING
            message = f"UI components available: {', '.join(available.keys())}"
            if missing:
                message += f" (Missing: {', '.join(missing)})"
                
            self.results.append(CheckResult(
                "UI Components",
                status,
                message,
                {"available": available, "missing": missing}
            ))
        else:
            self.results.append(CheckResult(
                "UI Components",
                Status.ERROR,
                f"No UI components available. Missing: {', '.join(missing)}",
                {"missing": missing}
            ))
    
    def check_security(self):
        """Check security components."""
        try:
            from core.security import SecurityManager
            from main import load_config
            
            config = load_config()
            security = SecurityManager(config)
            
            # Check whitelist file
            whitelist_file = self.project_root / "config/whitelist.yaml"
            if whitelist_file.exists():
                whitelist_status = Status.OK
                whitelist_msg = "Security manager and whitelist available"
            else:
                whitelist_status = Status.WARNING
                whitelist_msg = "Security manager OK, no whitelist file"
            
            self.results.append(CheckResult(
                "Security",
                whitelist_status,
                whitelist_msg
            ))
            
        except Exception as e:
            self.results.append(CheckResult(
                "Security",
                Status.ERROR,
                f"Security system error: {e}"
            ))
    
    def print_summary(self):
        """Print check summary."""
        print()
        print("📊 INTEGRITY CHECK RESULTS")
        print("=" * 50)
        
        for result in self.results:
            print(f"{result.status.value} {result.component}: {result.message}")
        
        print()
        
        # Count results
        ok_count = sum(1 for r in self.results if r.status == Status.OK)
        warning_count = sum(1 for r in self.results if r.status == Status.WARNING)
        error_count = sum(1 for r in self.results if r.status == Status.ERROR)
        
        print(f"Summary: {ok_count} OK, {warning_count} Warnings, {error_count} Errors")
        
        if error_count == 0:
            print("🎉 System integrity check passed!")
        else:
            print(f"⚠️  {error_count} critical issues found. Please address before running Jarvis.")
    
    def get_overall_status(self) -> Status:
        """Get overall system status."""
        if any(r.status == Status.ERROR for r in self.results):
            return Status.ERROR
        elif any(r.status == Status.WARNING for r in self.results):
            return Status.WARNING
        else:
            return Status.OK
