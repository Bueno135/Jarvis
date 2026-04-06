"""
Base plugin class with common functionality.
Provides a foundation for all Jarvis plugins with shared utilities.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from core.interfaces import PluginBase, CommandContext, CommandResult
from core.exceptions import PluginError, ValidationError, handle_exception
import logging

# This is a base class, not a plugin - mark it to avoid auto-loading
class BasePlugin(PluginBase):
    """Base class with common plugin functionality."""
    
    # Mark as abstract to prevent instantiation
    __is_abstract__ = True
    
    def __init__(self):
        self.logger = logging.getLogger(f"Jarvis.Plugin.{self.name()}")
        
    def validate_context(self, ctx: CommandContext) -> bool:
        """Validate command context before execution."""
        return True
        
    def get_help(self) -> str:
        """Return help text for this plugin."""
        return f"Plugin: {self.name()}\nPatterns: {', '.join(self.patterns())}"
        
    def cleanup(self):
        """Cleanup resources when plugin is unloaded."""
        pass
        
    @handle_exception
    def execute(self, ctx: CommandContext) -> CommandResult:
        """Execute with standardized error handling."""
        # Validate context
        if not self.validate_context(ctx):
            raise ValidationError(f"Invalid context for plugin {self.name()}")
            
        # Call the actual implementation
        try:
            return self._execute_impl(ctx)
        except Exception as e:
            self.logger.error(f"Execution failed in {self.name()}: {e}")
            raise PluginError(f"Execution failed: {e}", self.name())
            
    @abstractmethod
    def _execute_impl(self, ctx: CommandContext) -> CommandResult:
        """Actual implementation of the plugin logic."""
        pass
        
    def log_execution(self, ctx: CommandContext, result: CommandResult):
        """Log execution details."""
        self.logger.info(f"Executed {ctx.command_name}: {result.success} - {result.message}")
        
    def get_plugin_info(self) -> Dict[str, Any]:
        """Return plugin metadata."""
        return {
            "name": self.name(),
            "patterns": self.patterns(),
            "help": self.get_help(),
            "type": self.__class__.__name__
        }
