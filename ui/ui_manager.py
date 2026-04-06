"""
Unified UI manager for Jarvis.
Coordinates tray, overlay, and other UI components.
"""
import threading
import logging
from typing import Optional, Dict, Any
from core.kernel import Kernel
from core.exceptions import JarvisException, handle_exception

class UIManager:
    """Unified UI manager for Jarvis system."""
    
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.logger = logging.getLogger("Jarvis.UIManager")
        self.tray = None
        self.overlay = None
        self.is_running = False
        self.ui_components = {}
        
    def start(self):
        """Start all UI components."""
        if self.is_running:
            self.logger.warning("UI Manager already running")
            return
            
        self.logger.info("Starting UI components...")
        
        try:
            # Start overlay in separate thread
            self._start_overlay()
            
            # Start tray in main thread (blocking)
            self._start_tray()
            
        except Exception as e:
            self.logger.error(f"Failed to start UI: {e}")
            raise JarvisException(f"UI startup failed: {e}")
            
    def _start_overlay(self):
        """Start overlay UI component."""
        try:
            from ui.overlay import OverlayUI
            
            self.overlay = OverlayUI(self.kernel)
            overlay_thread = threading.Thread(
                target=self._run_overlay, 
                name="OverlayUI", 
                daemon=True
            )
            overlay_thread.start()
            self.ui_components["overlay"] = {
                "instance": self.overlay,
                "thread": overlay_thread,
                "status": "running"
            }
            self.logger.info("Overlay UI started")
            
        except ImportError as e:
            self.logger.warning(f"Overlay UI not available: {e}")
        except Exception as e:
            self.logger.error(f"Failed to start overlay: {e}")
            
    def _run_overlay(self):
        """Run overlay in thread."""
        try:
            self.overlay.run()
        except Exception as e:
            self.logger.error(f"Overlay error: {e}")
            
    def _start_tray(self):
        """Start system tray component."""
        try:
            from ui.tray import SystemTray
            
            self.tray = SystemTray(self.kernel)
            self.ui_components["tray"] = {
                "instance": self.tray,
                "status": "running"
            }
            self.logger.info("System tray started")
            
            # This is blocking - will run in main thread
            self.tray.run()
            
        except ImportError as e:
            self.logger.warning(f"System tray not available: {e}")
        except Exception as e:
            self.logger.error(f"Failed to start tray: {e}")
            
    def stop(self):
        """Stop all UI components."""
        self.logger.info("Stopping UI components...")
        
        # Stop tray
        if self.tray and hasattr(self.tray, 'stop'):
            try:
                self.tray.stop()
                self.logger.info("System tray stopped")
            except Exception as e:
                self.logger.error(f"Error stopping tray: {e}")
                
        # Stop overlay
        if self.overlay and hasattr(self.overlay, 'stop'):
            try:
                self.overlay.stop()
                self.logger.info("Overlay stopped")
            except Exception as e:
                self.logger.error(f"Error stopping overlay: {e}")
                
        self.is_running = False
        
    def get_status(self) -> Dict[str, Any]:
        """Get status of all UI components."""
        status = {
            "running": self.is_running,
            "components": {}
        }
        
        for name, component in self.ui_components.items():
            status["components"][name] = {
                "status": component.get("status", "unknown"),
                "type": type(component.get("instance")).__name__ if component.get("instance") else None
            }
            
        return status
        
    def show_notification(self, title: str, message: str, duration: int = 3000):
        """Show notification across all UI components."""
        self.logger.info(f"Notification: {title} - {message}")
        
        # Try tray notification
        if self.tray and hasattr(self.tray, 'notify'):
            try:
                self.tray.notify(title, message)
            except Exception as e:
                self.logger.error(f"Tray notification failed: {e}")
                
        # Try overlay notification
        if self.overlay and hasattr(self.overlay, 'show_notification'):
            try:
                self.overlay.show_notification(title, message, duration)
            except Exception as e:
                self.logger.error(f"Overlay notification failed: {e}")
                
    def update_status(self, status_text: str, state: str = None):
        """Update status display across UI components."""
        self.logger.info(f"Status update: {status_text}")
        
        # Update overlay
        if self.overlay and hasattr(self.overlay, 'update_status'):
            try:
                self.overlay.update_status(status_text, state)
            except Exception as e:
                self.logger.error(f"Overlay status update failed: {e}")
                
        # Update tray
        if self.tray and hasattr(self.tray, 'update_status'):
            try:
                self.tray.update_status(status_text)
            except Exception as e:
                self.logger.error(f"Tray status update failed: {e}")
                
    def handle_command_result(self, result: Any):
        """Handle command result and update UI accordingly."""
        if hasattr(result, 'success'):
            if result.success:
                self.show_notification("Success", result.message)
            else:
                self.show_notification("Error", result.message)
                
    def get_user_input(self, prompt: str, input_type: str = "text") -> Optional[str]:
        """Get user input through UI components."""
        # Try overlay first
        if self.overlay and hasattr(self.overlay, 'get_input'):
            try:
                return self.overlay.get_input(prompt, input_type)
            except Exception as e:
                self.logger.error(f"Overlay input failed: {e}")
                
        # Fallback to console
        try:
            return input(f"{prompt}: ")
        except (EOFError, KeyboardInterrupt):
            return None
