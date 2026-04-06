"""
Advanced Jarvis Examples
Demonstrates sophisticated usage patterns and integrations.
"""
import sys
import time
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import load_config
from core.kernel import Kernel
from core.interfaces import CommandContext, CommandResult
from core.cache import cache_result, get_cache_instance
from core.task_scheduler import get_task_scheduler, scheduled_task, Task, ScheduleType, TaskPriority
from core.continuous_learning import get_continuous_learning
from core.advanced_nlp import get_nlp_processor
from core.web_interface import create_web_interface
from core.security import SecurityManager, AutonomyMode

# Example 1: Custom Plugin with Advanced Features
class SmartHomePlugin:
    """Advanced smart home automation plugin."""
    
    def __init__(self):
        self.devices = {
            "living_room_light": {"status": "off", "brightness": 100},
            "bedroom_light": {"status": "off", "brightness": 50},
            "thermostat": {"temperature": 22, "mode": "auto"},
            "security_system": {"armed": False, "mode": "home"}
        }
        self.scenes = {
            "movie": {"living_room_light": {"status": "off"}, "thermostat": {"temperature": 20}},
            "sleep": {"living_room_light": {"status": "off"}, "bedroom_light": {"status": "off"}},
            "away": {"security_system": {"armed": True, "mode": "away"}}
        }
    
    @cache_result(ttl=300, tags=["smarthome"])
    def get_device_status(self, device_name: str) -> Dict[str, Any]:
        """Get device status with caching."""
        return self.devices.get(device_name, {})
    
    def control_device(self, device_name: str, action: str, value: Any = None) -> bool:
        """Control a smart home device."""
        if device_name not in self.devices:
            return False
        
        device = self.devices[device_name]
        
        if action == "turn_on":
            device["status"] = "on"
        elif action == "turn_off":
            device["status"] = "off"
        elif action == "set_brightness" and value:
            device["brightness"] = value
        elif action == "set_temperature" and value:
            device["temperature"] = value
        elif action == "arm_security":
            device["armed"] = True
        elif action == "disarm_security":
            device["armed"] = False
        else:
            return False
        
        return True
    
    def activate_scene(self, scene_name: str) -> bool:
        """Activate a predefined scene."""
        if scene_name not in self.scenes:
            return False
        
        scene = self.scenes[scene_name]
        for device_name, settings in scene.items():
            if device_name in self.devices:
                self.devices[device_name].update(settings)
        
        return True
    
    def get_energy_usage(self) -> Dict[str, float]:
        """Calculate energy usage for all devices."""
        usage = {}
        for device_name, device in self.devices.items():
            if device.get("status") == "on":
                if "light" in device_name:
                    usage[device_name] = device.get("brightness", 100) * 0.01  # kW
                elif device_name == "thermostat":
                    usage[device_name] = 2.0  # kW
        
        return usage

# Example 2: Advanced Task Automation
class TaskAutomationManager:
    """Manages complex task automations."""
    
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.scheduler = get_task_scheduler()
        self.learning = get_continuous_learning()
        self.automations = {}
    
    def create_automation(self, name: str, triggers: List[str], actions: List[str], 
                         conditions: List[str] = None) -> bool:
        """Create a new automation."""
        automation = {
            "name": name,
            "triggers": triggers,
            "actions": actions,
            "conditions": conditions or [],
            "enabled": True,
            "created_at": time.time()
        }
        
        self.automations[name] = automation
        return True
    
    def trigger_automation(self, trigger: str, context: Dict[str, Any] = None) -> List[str]:
        """Trigger automations based on a trigger event."""
        triggered_automations = []
        
        for name, automation in self.automations.items():
            if not automation["enabled"]:
                continue
            
            if trigger in automation["triggers"]:
                # Check conditions
                if self._check_conditions(automation["conditions"], context):
                    # Execute actions
                    for action in automation["actions"]:
                        self.kernel.dispatch(action)
                    
                    triggered_automations.append(name)
        
        return triggered_automations
    
    def _check_conditions(self, conditions: List[str], context: Dict[str, Any]) -> bool:
        """Check if automation conditions are met."""
        if not conditions:
            return True
        
        for condition in conditions:
            # Simple condition checking (in practice, this would be more sophisticated)
            if "time" in condition and context:
                current_hour = time.localtime().tm_hour
                if "morning" in condition and not (6 <= current_hour < 12):
                    return False
                elif "evening" in condition and not (18 <= current_hour < 22):
                    return False
        
        return True

# Example 3: Advanced NLP Integration
class ConversationManager:
    """Manages natural conversations with context awareness."""
    
    def __init__(self):
        self.nlp = get_nlp_processor()
        self.learning = get_continuous_learning()
        self.conversations = {}
    
    def start_conversation(self, user_id: str) -> str:
        """Start a new conversation."""
        context = self.nlp.create_context(user_id, f"conv_{int(time.time())}")
        self.conversations[user_id] = context
        
        return "Olá! Como posso ajudar você hoje?"
    
    def process_message(self, user_id: str, message: str) -> str:
        """Process a message in conversation context."""
        if user_id not in self.conversations:
            return self.start_conversation(user_id)
        
        context = self.conversations[user_id]
        intent = self.nlp.process_text(message, context)
        
        # Handle different intent types
        if intent.type.value == "greeting":
            return "Olá! Estou aqui para ajudar."
        elif intent.type.value == "farewell":
            return "Até logo! Foi um prazer ajudar."
        elif intent.type.value == "question":
            return self._handle_question(intent)
        elif intent.type.value == "command":
            return self._handle_command(intent)
        else:
            return "Não entendi. Pode reformular?"
    
    def _handle_question(self, intent) -> str:
        """Handle question intents."""
        if "time" in intent.parameters:
            current_time = time.strftime("%H:%M")
            return f"Agora são {current_time}."
        elif "weather" in intent.parameters:
            return "Desculpe, ainda não tenho acesso a informações do tempo."
        else:
            return "Essa é uma boa pergunta. Deixe me pensar..."
    
    def _handle_command(self, intent) -> str:
        """Handle command intents."""
        # This would integrate with the kernel
        return f"Entendi o comando: {intent.name}"

# Example 4: Performance Monitoring and Optimization
class PerformanceMonitor:
    """Monitors and optimizes system performance."""
    
    def __init__(self):
        self.metrics = []
        self.alerts = []
        self.thresholds = {
            "response_time": 2.0,  # seconds
            "memory_usage": 0.8,    # 80%
            "cpu_usage": 0.9,      # 90%
            "error_rate": 0.05     # 5%
        }
    
    def record_metric(self, metric_name: str, value: float, metadata: Dict[str, Any] = None):
        """Record a performance metric."""
        metric = {
            "name": metric_name,
            "value": value,
            "timestamp": time.time(),
            "metadata": metadata or {}
        }
        
        self.metrics.append(metric)
        
        # Check for alerts
        self._check_alerts(metric)
        
        # Keep only recent metrics (last 1000)
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
    
    def _check_alerts(self, metric: Dict[str, Any]):
        """Check if metric exceeds thresholds."""
        name = metric["name"]
        value = metric["value"]
        
        if name in self.thresholds and value > self.thresholds[name]:
            alert = {
                "type": "threshold_exceeded",
                "metric": name,
                "value": value,
                "threshold": self.thresholds[name],
                "timestamp": time.time()
            }
            
            self.alerts.append(alert)
            print(f"⚠️ Performance Alert: {name} = {value} (threshold: {self.thresholds[name]})")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        if not self.metrics:
            return {"status": "no_data"}
        
        # Calculate statistics
        response_times = [m["value"] for m in self.metrics if m["name"] == "response_time"]
        
        report = {
            "total_metrics": len(self.metrics),
            "active_alerts": len([a for a in self.alerts if time.time() - a["timestamp"] < 3600]),
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "recent_metrics": len([m for m in self.metrics if time.time() - m["timestamp"] < 300])
        }
        
        return report

# Example 5: Multi-Modal Integration
class MultiModalProcessor:
    """Processes multiple input modalities (voice, text, vision)."""
    
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.context_memory = {}
    
    def process_voice_input(self, audio_data: bytes, user_id: str = "default") -> str:
        """Process voice input and return response."""
        # This would integrate with STT
        text = self._transcribe_audio(audio_data)
        return self.process_text_input(text, user_id)
    
    def process_text_input(self, text: str, user_id: str = "default") -> str:
        """Process text input and return response."""
        # Get or create context
        context = self._get_context(user_id)
        
        # Process with NLP
        nlp = get_nlp_processor()
        intent = nlp.process_text(text, context)
        
        # Execute command
        result = self.kernel.dispatch(text)
        
        # Update context
        self._update_context(user_id, intent, result)
        
        return result.message
    
    def process_visual_input(self, image_data: bytes, query: str = None, user_id: str = "default") -> str:
        """Process visual input and return analysis."""
        # This would integrate with vision processing
        analysis = self._analyze_image(image_data)
        
        if query:
            # Process query about the image
            context = self._get_context(user_id)
            full_query = f"{query} (context: {analysis})"
            return self.process_text_input(full_query, user_id)
        else:
            return f"Análise da imagem: {analysis}"
    
    def _transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio to text (mock implementation)."""
        # This would use the actual STT system
        return "transcribed text from audio"
    
    def _analyze_image(self, image_data: bytes) -> str:
        """Analyze image content (mock implementation)."""
        # This would use the actual vision system
        return "detected objects: computer, keyboard, mouse"
    
    def _get_context(self, user_id: str):
        """Get or create user context."""
        if user_id not in self.context_memory:
            self.context_memory[user_id] = {
                "history": [],
                "preferences": {},
                "last_interaction": time.time()
            }
        return self.context_memory[user_id]
    
    def _update_context(self, user_id: str, intent, result):
        """Update user context."""
        if user_id in self.context_memory:
            context = self.context_memory[user_id]
            context["history"].append({
                "intent": intent.name,
                "result": result.success,
                "timestamp": time.time()
            })
            context["last_interaction"] = time.time()
            
            # Keep only last 10 interactions
            if len(context["history"]) > 10:
                context["history"] = context["history"][-10:]

# Example 6: Advanced Security and Privacy
class PrivacyManager:
    """Manages privacy settings and data protection."""
    
    def __init__(self):
        self.privacy_settings = {
            "record_interactions": True,
            "share_analytics": False,
            "retention_days": 30,
            "anonymize_data": True,
            "encryption_enabled": True
        }
        self.consent_records = {}
    
    def set_privacy_setting(self, setting: str, value: bool, user_id: str = "default") -> bool:
        """Update privacy setting with user consent."""
        if setting not in self.privacy_settings:
            return False
        
        # Record consent
        self.consent_records[user_id] = self.consent_records.get(user_id, {})
        self.consent_records[user_id][setting] = {
            "value": value,
            "timestamp": time.time(),
            "ip_address": "127.0.0.1"  # In practice, get actual IP
        }
        
        self.privacy_settings[setting] = value
        return True
    
    def should_record_interaction(self, user_id: str = "default") -> bool:
        """Check if interaction should be recorded based on privacy settings."""
        if not self.privacy_settings["record_interactions"]:
            return False
        
        # Check user consent
        if user_id in self.consent_records:
            return self.consent_records[user_id].get("record_interactions", {}).get("value", False)
        
        return False
    
    def anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize sensitive data."""
        if not self.privacy_settings["anonymize_data"]:
            return data
        
        anonymized = data.copy()
        
        # Remove or hash sensitive fields
        sensitive_fields = ["user_id", "ip_address", "email", "phone"]
        for field in sensitive_fields:
            if field in anonymized:
                anonymized[field] = hashlib.sha256(str(anonymized[field]).encode()).hexdigest()[:16]
        
        return anonymized
    
    def cleanup_old_data(self):
        """Clean up data older than retention period."""
        retention_seconds = self.privacy_settings["retention_days"] * 24 * 3600
        cutoff_time = time.time() - retention_seconds
        
        # This would clean up old interaction logs, memory data, etc.
        print(f"Cleaning up data older than {self.privacy_settings['retention_days']} days")

# Example 7: Integration Demo
def demonstrate_advanced_integration():
    """Demonstrate all advanced features working together."""
    print("🚀 Advanced Jarvis Integration Demo")
    print("=" * 50)
    
    # Initialize kernel
    config = load_config()
    kernel = Kernel(config)
    
    # Initialize advanced components
    smarthome = SmartHomePlugin()
    automation = TaskAutomationManager(kernel)
    conversation = ConversationManager()
    performance = PerformanceMonitor()
    multimodal = MultiModalProcessor(kernel)
    privacy = PrivacyManager()
    
    # Demo 1: Smart Home Integration
    print("\n🏠 Smart Home Demo:")
    smarthome.control_device("living_room_light", "turn_on")
    smarthome.control_device("thermostat", "set_temperature", 23)
    print(f"Living room light: {smarthome.get_device_status('living_room_light')}")
    print(f"Thermostat: {smarthome.get_device_status('thermostat')}")
    print(f"Energy usage: {smarthome.get_energy_usage()}")
    
    # Demo 2: Task Automation
    print("\n⚡ Task Automation Demo:")
    automation.create_automation(
        name="evening_routine",
        triggers=["time_evening", "user_home"],
        actions=["turn on living room light", "set thermostat to 22"],
        conditions=["time_evening"]
    )
    
    triggered = automation.trigger_automation("time_evening", {"time": "evening"})
    print(f"Triggered automations: {triggered}")
    
    # Demo 3: Natural Conversation
    print("\n💬 Conversation Demo:")
    user_id = "demo_user"
    greeting = conversation.start_conversation(user_id)
    print(f"Jarvis: {greeting}")
    
    responses = [
        conversation.process_message(user_id, "que horas são?"),
        conversation.process_message(user_id, "abra o notepad"),
        conversation.process_message(user_id, "obrigado")
    ]
    
    for response in responses:
        print(f"User: message")
        print(f"Jarvis: {response}")
    
    # Demo 4: Performance Monitoring
    print("\n📊 Performance Monitoring Demo:")
    performance.record_metric("response_time", 0.5)
    performance.record_metric("response_time", 0.8)
    performance.record_metric("response_time", 1.2)
    performance.record_metric("memory_usage", 0.7)
    
    report = performance.get_performance_report()
    print(f"Performance report: {report}")
    
    # Demo 5: Multi-Modal Processing
    print("\n👁️ Multi-Modal Demo:")
    text_response = multimodal.process_text_input("mostre o clima", user_id)
    print(f"Text response: {text_response}")
    
    # Demo 6: Privacy Management
    print("\n🔒 Privacy Management Demo:")
    privacy.set_privacy_setting("record_interactions", True, user_id)
    privacy.set_privacy_setting("share_analytics", False, user_id)
    
    should_record = privacy.should_record_interaction(user_id)
    print(f"Should record interactions: {should_record}")
    
    # Demo 7: Scheduled Tasks
    print("\n⏰ Scheduled Tasks Demo:")
    scheduler = get_task_scheduler()
    
    def daily_report():
        """Generate daily performance report."""
        report = performance.get_performance_report()
        print(f"📈 Daily Report: {report}")
        return "Report generated"
    
    # Schedule daily report
    task = Task(
        id="daily_report",
        name="Daily Performance Report",
        description="Generate daily performance metrics",
        function=daily_report,
        schedule_type=ScheduleType.DAILY,
        schedule_params={"time": "23:59"},
        priority=TaskPriority.NORMAL
    )
    
    scheduler.add_task(task)
    print("Daily report task scheduled")
    
    print("\n🎉 Advanced integration demo completed!")
    print("All systems working together seamlessly.")

# Example 8: Custom Plugin with All Features
class AdvancedAssistantPlugin:
    """An advanced assistant plugin showcasing all features."""
    
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.cache = get_cache_instance()
        self.learning = get_continuous_learning()
        self.nlp = get_nlp_processor()
        self.performance = PerformanceMonitor()
    
    @cache_result(ttl=300, tags=["assistant"])
    def get_assistant_status(self) -> Dict[str, Any]:
        """Get comprehensive assistant status."""
        return {
            "uptime": time.time() - getattr(self.kernel, 'start_time', time.time()),
            "plugins_loaded": len(self.kernel.plugins),
            "memory_usage": self._get_memory_usage(),
            "performance": self.performance.get_performance_report()
        }
    
    def process_complex_request(self, request: str, user_id: str = "default") -> Dict[str, Any]:
        """Process a complex multi-step request."""
        start_time = time.time()
        
        try:
            # Parse request with NLP
            context = self.nlp.create_context(user_id, f"complex_{int(time.time())}")
            intent = self.nlp.process_text(request, context)
            
            # Execute based on intent
            if intent.name == "status_report":
                result = self.get_assistant_status()
            elif intent.name == "performance_analysis":
                result = self._analyze_performance()
            elif intent.name == "system_optimization":
                result = self._optimize_system()
            else:
                result = self.kernel.dispatch(request)
            
            # Record performance
            response_time = time.time() - start_time
            self.performance.record_metric("response_time", response_time)
            
            # Record for learning
            from core.interfaces import CommandContext, CommandResult
            ctx = CommandContext(
                raw_text=request,
                command_name=intent.name,
                parameters=intent.parameters,
                kernel=self.kernel
            )
            
            cmd_result = CommandResult(
                success=True,
                message=str(result),
                data=result
            )
            
            self.learning.record_interaction(ctx, cmd_result, response_time, user_id)
            
            return {
                "success": True,
                "result": result,
                "intent": intent.name,
                "response_time": response_time
            }
            
        except Exception as e:
            self.performance.record_metric("error_count", 1)
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage."""
        import psutil
        memory = psutil.virtual_memory()
        return {
            "used_percent": memory.percent,
            "used_gb": memory.used / (1024**3),
            "total_gb": memory.total / (1024**3)
        }
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze system performance."""
        report = self.performance.get_performance_report()
        
        # Add recommendations
        recommendations = []
        
        if report.get("avg_response_time", 0) > 1.0:
            recommendations.append("Consider optimizing slow operations")
        
        if report.get("active_alerts", 0) > 0:
            recommendations.append("Address active performance alerts")
        
        report["recommendations"] = recommendations
        return report
    
    def _optimize_system(self) -> Dict[str, Any]:
        """Perform system optimization."""
        optimizations = []
        
        # Clear cache if it's getting large
        cache_stats = self.cache.get_stats()
        if cache_stats.get("memory_entries", 0) > 50:
            self.cache.clear()
            optimizations.append("Cleared cache")
        
        # Trigger garbage collection
        import gc
        collected = gc.collect()
        if collected > 0:
            optimizations.append(f"Garbage collected {collected} objects")
        
        return {
            "optimizations": optimizations,
            "performance_after": self.performance.get_performance_report()
        }

if __name__ == "__main__":
    # Run the advanced integration demo
    demonstrate_advanced_integration()
    
    print("\n📚 Additional Examples Available:")
    print("- Smart Home Integration")
    print("- Task Automation")
    print("- Natural Conversation")
    print("- Performance Monitoring")
    print("- Multi-Modal Processing")
    print("- Privacy Management")
    print("- Advanced Assistant Plugin")
    
    print("\n💡 Try running individual examples:")
    print("python examples/advanced_features.py")
    print("python examples/basic_usage.py")
