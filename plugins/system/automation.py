import re
import os
import logging
from typing import List, Dict, Any, Optional
from core.interfaces import PluginBase, CommandContext, CommandResult

# Lazy import pyautogui — requires DISPLAY on Linux
_pyautogui = None

def _get_pyautogui():
    global _pyautogui
    if _pyautogui is None:
        import pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5
        _pyautogui = pyautogui
    return _pyautogui

logger = logging.getLogger("Jarvis.Automation")


class AutomationPlugin(PluginBase):
    """
    Plugin for controlling mouse and keyboard automation using pyautogui.
    Supports clicking, typing, keyboard hotkeys, mouse movement, and scrolling.
    """

    def name(self) -> str:
        return "Automation"

    def patterns(self) -> List[str]:
        return [
            "click",
            "double click",
            "type text",
            "move mouse",
            "scroll",
            "press key",
            "hotkey"
        ]

    def intents(self) -> List[str]:
        """
        Returns the list of supported intents for this plugin.
        """
        return [
            "mouse_click",
            "double_click",
            "keyboard_type",
            "hotkey_press",
            "mouse_move",
            "mouse_scroll"
        ]

    def execute(self, ctx: CommandContext) -> CommandResult:
        """
        Execute automation actions based on intent or raw text parsing.
        """
        try:
            # Determine the intent/action to perform
            command_name = ctx.command_name.lower() if ctx.command_name else ""
            intent = None

            # Check if intent is provided in command_name
            if command_name in self.intents():
                intent = command_name

            # Try to infer from raw_text if no explicit intent
            if not intent:
                intent = self._infer_intent(ctx.raw_text)

            if not intent:
                return CommandResult(
                    False,
                    "Could not determine automation action from command or text."
                )

            # Dispatch to appropriate action handler
            if intent == "mouse_click":
                return self._handle_mouse_click(ctx.params, ctx.raw_text)
            elif intent == "double_click":
                return self._handle_double_click(ctx.params, ctx.raw_text)
            elif intent == "keyboard_type":
                return self._handle_keyboard_type(ctx.params, ctx.raw_text)
            elif intent == "hotkey_press":
                return self._handle_hotkey_press(ctx.params, ctx.raw_text)
            elif intent == "mouse_move":
                return self._handle_mouse_move(ctx.params, ctx.raw_text)
            elif intent == "mouse_scroll":
                return self._handle_mouse_scroll(ctx.params, ctx.raw_text)
            else:
                return CommandResult(False, f"Unknown intent: {intent}")

        except Exception as e:
            logger.error(f"Automation plugin error: {str(e)}")
            return CommandResult(False, f"Automation error: {str(e)}")

    def _infer_intent(self, raw_text: str) -> Optional[str]:
        """
        Infer the automation intent from raw text.
        """
        text_lower = raw_text.lower()

        if "double click" in text_lower or "double-click" in text_lower:
            return "double_click"
        elif "click" in text_lower:
            return "mouse_click"
        elif "type" in text_lower or "write" in text_lower:
            return "keyboard_type"
        elif "hotkey" in text_lower or "key combination" in text_lower:
            return "hotkey_press"
        elif "move mouse" in text_lower or "move cursor" in text_lower:
            return "mouse_move"
        elif "scroll" in text_lower:
            return "mouse_scroll"
        elif "press key" in text_lower or "press" in text_lower:
            return "hotkey_press"

        return None

    def _handle_mouse_click(self, params: Dict[str, Any], raw_text: str) -> CommandResult:
        """
        Handle mouse click action at specified coordinates.
        """
        x, y = self._get_coordinates(params, raw_text)

        if x is None or y is None:
            return CommandResult(False, "Could not parse click coordinates from params or text.")

        try:
            _get_pyautogui().click(x, y)
            logger.info(f"Clicked at coordinates ({x}, {y})")
            return CommandResult(True, f"Clicked at ({x}, {y})")
        except Exception as e:
            logger.error(f"Click failed at ({x}, {y}): {str(e)}")
            return CommandResult(False, f"Click failed: {str(e)}")

    def _handle_double_click(self, params: Dict[str, Any], raw_text: str) -> CommandResult:
        """
        Handle double-click action at specified coordinates.
        """
        x, y = self._get_coordinates(params, raw_text)

        if x is None or y is None:
            return CommandResult(False, "Could not parse double-click coordinates from params or text.")

        try:
            _get_pyautogui().doubleClick(x, y)
            logger.info(f"Double-clicked at coordinates ({x}, {y})")
            return CommandResult(True, f"Double-clicked at ({x}, {y})")
        except Exception as e:
            logger.error(f"Double-click failed at ({x}, {y}): {str(e)}")
            return CommandResult(False, f"Double-click failed: {str(e)}")

    def _handle_keyboard_type(self, params: Dict[str, Any], raw_text: str) -> CommandResult:
        """
        Handle keyboard typing action.
        """
        text = self._get_text_to_type(params, raw_text)

        if not text:
            return CommandResult(False, "Could not determine text to type.")

        try:
            # Use write with interval for safety and readability
            _get_pyautogui().write(text, interval=0.05)
            logger.info(f"Typed text: {text[:50]}{'...' if len(text) > 50 else ''}")
            return CommandResult(True, f"Typed {len(text)} characters")
        except Exception as e:
            logger.error(f"Keyboard type failed: {str(e)}")
            return CommandResult(False, f"Type failed: {str(e)}")

    def _handle_hotkey_press(self, params: Dict[str, Any], raw_text: str) -> CommandResult:
        """
        Handle keyboard hotkey combination (e.g., Ctrl+C, Alt+Tab).
        """
        keys = self._get_hotkey_keys(params, raw_text)

        if not keys:
            return CommandResult(False, "Could not determine hotkey keys.")

        try:
            # Convert to lowercase for pyautogui compatibility
            keys_lower = [k.lower() for k in keys]
            _get_pyautogui().hotkey(*keys_lower)
            logger.info(f"Pressed hotkey: {'+'.join(keys)}")
            return CommandResult(True, f"Pressed hotkey: {'+'.join(keys)}")
        except Exception as e:
            logger.error(f"Hotkey press failed ({keys}): {str(e)}")
            return CommandResult(False, f"Hotkey press failed: {str(e)}")

    def _handle_mouse_move(self, params: Dict[str, Any], raw_text: str) -> CommandResult:
        """
        Handle mouse movement to specified coordinates.
        """
        x, y = self._get_coordinates(params, raw_text)

        if x is None or y is None:
            return CommandResult(False, "Could not parse mouse move coordinates from params or text.")

        try:
            _get_pyautogui().moveTo(x, y)
            logger.info(f"Moved mouse to ({x}, {y})")
            return CommandResult(True, f"Moved mouse to ({x}, {y})")
        except Exception as e:
            logger.error(f"Mouse move failed to ({x}, {y}): {str(e)}")
            return CommandResult(False, f"Mouse move failed: {str(e)}")

    def _handle_mouse_scroll(self, params: Dict[str, Any], raw_text: str) -> CommandResult:
        """
        Handle mouse scroll action.
        """
        amount = self._get_scroll_amount(params, raw_text)

        if amount is None:
            return CommandResult(False, "Could not determine scroll amount.")

        try:
            _get_pyautogui().scroll(amount)
            direction = "up" if amount > 0 else "down"
            logger.info(f"Scrolled {direction} by {abs(amount)} units")
            return CommandResult(True, f"Scrolled {direction} by {abs(amount)} units")
        except Exception as e:
            logger.error(f"Mouse scroll failed: {str(e)}")
            return CommandResult(False, f"Scroll failed: {str(e)}")

    # Helper methods for parsing parameters and raw text

    def _get_coordinates(self, params: Dict[str, Any], raw_text: str) -> tuple:
        """
        Extract x, y coordinates from params or raw text.
        Returns (x, y) or (None, None) if not found.
        """
        # Try to get from params first
        if params:
            x = params.get("x")
            y = params.get("y")
            if x is not None and y is not None:
                try:
                    return (int(x), int(y))
                except (ValueError, TypeError):
                    pass

        # Try to parse from raw_text using regex
        # Patterns: "click at 100 200", "at x:100 y:200", "at (100, 200)"
        patterns = [
            r"(?:at|to)\s+(\d+)\s+(\d+)",  # "at 100 200" or "to 100 200"
            r"x[:\s]+(\d+)[,\s]+y[:\s]+(\d+)",  # "x: 100, y: 200"
            r"\((\d+)\s*,\s*(\d+)\)",  # "(100, 200)"
        ]

        for pattern in patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                try:
                    x, y = int(match.group(1)), int(match.group(2))
                    return (x, y)
                except (ValueError, IndexError):
                    continue

        return (None, None)

    def _get_text_to_type(self, params: Dict[str, Any], raw_text: str) -> Optional[str]:
        """
        Extract text to type from params or raw text.
        """
        # Try to get from params first
        if params:
            text = params.get("text")
            if text:
                return str(text)

        # Try to parse from raw_text
        # Patterns: "type hello world", "type 'hello world'", "type \"hello\""
        patterns = [
            r"type\s+['\"](.+?)['\"]",  # type "text" or type 'text'
            r"type\s+(.+)$",  # type text (rest of line)
            r"write\s+['\"](.+?)['\"]",  # write "text" or write 'text'
            r"write\s+(.+)$",  # write text (rest of line)
        ]

        for pattern in patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                text = match.group(1).strip()
                if text:
                    return text

        return None

    def _get_hotkey_keys(self, params: Dict[str, Any], raw_text: str) -> Optional[List[str]]:
        """
        Extract hotkey keys from params or raw text.
        Expected format: ['ctrl', 'c'] or 'ctrl+c' or 'ctrl c'
        """
        # Try to get from params first
        if params:
            keys = params.get("keys")
            if keys:
                if isinstance(keys, list):
                    return keys
                elif isinstance(keys, str):
                    # Parse string like "ctrl+c" or "ctrl c"
                    return re.split(r'[+\s]+', keys.lower())

        # Try to parse from raw_text
        # Patterns: "press ctrl+c", "hotkey ctrl c", etc.
        patterns = [
            r"(?:press|hotkey)\s+([a-z]+[+\s][a-z]+(?:[+\s][a-z]+)*)",  # hotkey ctrl+c or press ctrl c
            r"(?:keys?)\s+([a-z]+[+\s][a-z]+(?:[+\s][a-z]+)*)",  # keys ctrl+c
        ]

        for pattern in patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                keys_str = match.group(1)
                # Split by + or space
                keys = re.split(r'[+\s]+', keys_str.lower())
                if keys:
                    return keys

        return None

    def _get_scroll_amount(self, params: Dict[str, Any], raw_text: str) -> Optional[int]:
        """
        Extract scroll amount from params or raw text.
        Positive = scroll up, negative = scroll down.
        """
        # Try to get from params first
        if params:
            amount = params.get("amount")
            if amount is not None:
                try:
                    return int(amount)
                except (ValueError, TypeError):
                    pass

        # Try to parse from raw_text
        # Patterns: "scroll up 5", "scroll down 3", "scroll 10"
        patterns = [
            r"scroll\s+up\s+(\d+)",  # scroll up 5
            r"scroll\s+down\s+(\d+)",  # scroll down 3 -> negative
            r"scroll\s+(\d+)",  # scroll 10 (default up)
        ]

        for i, pattern in enumerate(patterns):
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                try:
                    amount = int(match.group(1))
                    # For "scroll down", make it negative
                    if "down" in pattern:
                        amount = -amount
                    return amount
                except (ValueError, IndexError):
                    continue

        return None
