"""
Success metrics and monitoring for Jarvis.
Tracks system performance, usage patterns, and health indicators.
"""
import time
import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    TIMER = "timer"
    HISTOGRAM = "histogram"

@dataclass
class Metric:
    """Base metric data structure."""
    name: str
    type: MetricType
    value: float
    timestamp: float
    labels: Dict[str, str] = None
    description: str = ""

@dataclass
class SystemMetrics:
    """System performance metrics."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    audio_latency: float
    plugin_load_time: float
    command_success_rate: float
    error_rate: float

@dataclass
class UsageMetrics:
    """Usage pattern metrics."""
    commands_executed: int
    voice_commands: int
    text_commands: int
    plugins_used: Dict[str, int]
    average_response_time: float
    daily_active_time: float

class MetricsCollector:
    """Collects and manages system metrics."""
    
    def __init__(self, metrics_dir: str = "metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(exist_ok=True)
        self.metrics: List[Metric] = []
        self.start_time = time.time()
        
    def record_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE, 
                     labels: Dict[str, str] = None, description: str = ""):
        """Record a metric."""
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            timestamp=time.time(),
            labels=labels or {},
            description=description
        )
        self.metrics.append(metric)
        
    def increment_counter(self, name: str, labels: Dict[str, str] = None, description: str = ""):
        """Increment a counter metric."""
        current_value = self.get_current_value(name, labels) or 0
        self.record_metric(name, current_value + 1, MetricType.COUNTER, labels, description)
        
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None, description: str = ""):
        """Set a gauge metric."""
        self.record_metric(name, value, MetricType.GAUGE, labels, description)
        
    def record_timer(self, name: str, duration: float, labels: Dict[str, str] = None, description: str = ""):
        """Record a timer metric."""
        self.record_metric(name, duration, MetricType.TIMER, labels, description)
        
    def get_current_value(self, name: str, labels: Dict[str, str] = None) -> Optional[float]:
        """Get current value for a metric."""
        for metric in reversed(self.metrics):
            if metric.name == name and metric.labels == (labels or {}):
                return metric.value
        return None
        
    def get_metrics_summary(self, time_window: float = 3600) -> Dict[str, Any]:
        """Get metrics summary for the last time_window seconds."""
        cutoff_time = time.time() - time_window
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
        
        summary = {
            "time_window": time_window,
            "total_metrics": len(recent_metrics),
            "metrics_by_type": {},
            "top_metrics": {}
        }
        
        # Group by type
        for metric_type in MetricType:
            type_metrics = [m for m in recent_metrics if m.type == metric_type]
            summary["metrics_by_type"][metric_type.value] = len(type_metrics)
        
        # Top metrics by frequency
        metric_counts = {}
        for metric in recent_metrics:
            metric_counts[metric.name] = metric_counts.get(metric.name, 0) + 1
        
        summary["top_metrics"] = dict(sorted(metric_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        return summary
        
    def save_metrics(self, filename: str = None):
        """Save metrics to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_{timestamp}.json"
        
        filepath = self.metrics_dir / filename
        
        # Convert metrics to serializable format
        serializable_metrics = []
        for metric in self.metrics:
            metric_dict = asdict(metric)
            metric_dict["type"] = metric.type.value
            serializable_metrics.append(metric_dict)
        
        with open(filepath, 'w') as f:
            json.dump(serializable_metrics, f, indent=2)
        
        return filepath

class SystemHealthMonitor:
    """Monitors system health and performance."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.health_checks = []
        
    def add_health_check(self, name: str, check_func, threshold: float = None):
        """Add a health check."""
        self.health_checks.append({
            "name": name,
            "check": check_func,
            "threshold": threshold
        })
        
    def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        overall_health = True
        
        for health_check in self.health_checks:
            try:
                result = health_check["check"]()
                passed = True
                
                if health_check["threshold"] is not None:
                    passed = result <= health_check["threshold"]
                
                results[health_check["name"]] = {
                    "value": result,
                    "passed": passed,
                    "threshold": health_check["threshold"]
                }
                
                if not passed:
                    overall_health = False
                    
            except Exception as e:
                results[health_check["name"]] = {
                    "value": None,
                    "passed": False,
                    "error": str(e)
                }
                overall_health = False
        
        results["overall_health"] = overall_health
        return results
        
    def check_cpu_usage(self) -> float:
        """Check CPU usage percentage."""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return 0.0
            
    def check_memory_usage(self) -> float:
        """Check memory usage percentage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.percent
        except ImportError:
            return 0.0
            
    def check_disk_usage(self) -> float:
        """Check disk usage percentage."""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            return (disk.used / disk.total) * 100
        except ImportError:
            return 0.0
            
    def check_audio_latency(self) -> float:
        """Check audio latency in milliseconds."""
        try:
            import sounddevice as sd
            start_time = time.time()
            sd.query_devices()
            return (time.time() - start_time) * 1000
        except ImportError:
            return 0.0

class SuccessMetrics:
    """Defines and tracks success metrics for Jarvis."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.health_monitor = SystemHealthMonitor(metrics_collector)
        self._setup_health_checks()
        
    def _setup_health_checks(self):
        """Setup default health checks."""
        self.health_monitor.add_health_check("cpu_usage", self.health_monitor.check_cpu_usage, 80.0)
        self.health_monitor.add_health_check("memory_usage", self.health_monitor.check_memory_usage, 85.0)
        self.health_monitor.add_health_check("disk_usage", self.health_monitor.check_disk_usage, 90.0)
        self.health_monitor.add_health_check("audio_latency", self.health_monitor.check_audio_latency, 100.0)
        
    def record_command_execution(self, command: str, success: bool, response_time: float, 
                                plugin_name: str = None, command_type: str = "text"):
        """Record command execution metrics."""
        # Basic counters
        self.metrics.increment_counter("commands_total", {"type": command_type})
        
        if success:
            self.metrics.increment_counter("commands_success", {"type": command_type})
        else:
            self.metrics.increment_counter("commands_failed", {"type": command_type})
        
        # Response time
        self.metrics.record_timer("command_response_time", response_time, 
                                {"type": command_type, "plugin": plugin_name or "unknown"})
        
        # Plugin usage
        if plugin_name:
            self.metrics.increment_counter("plugin_usage", {"plugin": plugin_name})
        
        # Command success rate
        total_commands = self.metrics.get_current_value("commands_total", {"type": command_type}) or 0
        successful_commands = self.metrics.get_current_value("commands_success", {"type": command_type}) or 0
        
        if total_commands > 0:
            success_rate = (successful_commands / total_commands) * 100
            self.metrics.set_gauge("command_success_rate", success_rate, {"type": command_type})
    
    def record_voice_interaction(self, wake_word_detected: bool, transcription_time: float, 
                               audio_quality: float = None):
        """Record voice interaction metrics."""
        self.metrics.increment_counter("voice_interactions_total")
        
        if wake_word_detected:
            self.metrics.increment_counter("wake_word_detections")
        
        self.metrics.record_timer("transcription_time", transcription_time)
        
        if audio_quality is not None:
            self.metrics.set_gauge("audio_quality", audio_quality)
    
    def record_plugin_performance(self, plugin_name: str, load_time: float, memory_usage: float = None):
        """Record plugin performance metrics."""
        self.metrics.record_timer("plugin_load_time", load_time, {"plugin": plugin_name})
        
        if memory_usage is not None:
            self.metrics.set_gauge("plugin_memory_usage", memory_usage, {"plugin": plugin_name})
    
    def record_system_resources(self):
        """Record system resource usage."""
        cpu_usage = self.health_monitor.check_cpu_usage()
        memory_usage = self.health_monitor.check_memory_usage()
        disk_usage = self.health_monitor.check_disk_usage()
        
        self.metrics.set_gauge("system_cpu_usage", cpu_usage)
        self.metrics.set_gauge("system_memory_usage", memory_usage)
        self.metrics.set_gauge("system_disk_usage", disk_usage)
    
    def record_error(self, error_type: str, component: str = None, severity: str = "medium"):
        """Record error metrics."""
        labels = {"type": error_type, "severity": severity}
        if component:
            labels["component"] = component
            
        self.metrics.increment_counter("errors_total", labels)
    
    def get_success_report(self, time_window: float = 3600) -> Dict[str, Any]:
        """Generate comprehensive success report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "time_window_hours": time_window / 3600,
            "system_health": self.health_monitor.run_health_checks(),
            "metrics_summary": self.metrics.get_metrics_summary(time_window),
            "key_indicators": {}
        }
        
        # Key success indicators
        indicators = {
            "uptime_hours": (time.time() - self.metrics.start_time) / 3600,
            "commands_per_hour": 0,
            "success_rate": 0,
            "average_response_time": 0,
            "error_rate": 0,
            "most_used_plugin": None
        }
        
        # Calculate indicators from metrics
        cutoff_time = time.time() - time_window
        recent_metrics = [m for m in self.metrics.metrics if m.timestamp >= cutoff_time]
        
        # Commands per hour
        total_commands = len([m for m in recent_metrics if m.name == "commands_total"])
        indicators["commands_per_hour"] = total_commands / (time_window / 3600)
        
        # Success rate
        success_metrics = [m for m in recent_metrics if m.name == "command_success_rate"]
        if success_metrics:
            indicators["success_rate"] = success_metrics[-1].value
        
        # Average response time
        response_times = [m.value for m in recent_metrics if m.name == "command_response_time"]
        if response_times:
            indicators["average_response_time"] = sum(response_times) / len(response_times)
        
        # Error rate
        total_errors = len([m for m in recent_metrics if m.name == "errors_total"])
        indicators["error_rate"] = (total_errors / max(total_commands, 1)) * 100
        
        # Most used plugin
        plugin_usage = {}
        for m in recent_metrics:
            if m.name == "plugin_usage" and m.labels:
                plugin = m.labels.get("plugin", "unknown")
                plugin_usage[plugin] = plugin_usage.get(plugin, 0) + 1
        
        if plugin_usage:
            indicators["most_used_plugin"] = max(plugin_usage, key=plugin_usage.get)
        
        report["key_indicators"] = indicators
        
        # Success criteria
        report["success_criteria"] = {
            "overall_health": report["system_health"]["overall_health"],
            "success_rate_above_80": indicators["success_rate"] >= 80,
            "response_time_below_2s": indicators["average_response_time"] < 2.0,
            "error_rate_below_10": indicators["error_rate"] < 10,
            "commands_per_hour_above_1": indicators["commands_per_hour"] > 1
        }
        
        # Overall success
        criteria_met = sum(report["success_criteria"].values())
        report["overall_success"] = criteria_met >= 4  # At least 4/5 criteria met
        
        return report
    
    def save_success_report(self, filename: str = None) -> str:
        """Save success report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"success_report_{timestamp}.json"
        
        report = self.get_success_report()
        filepath = Path("metrics") / filename
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        return str(filepath)

# Global metrics instance
_metrics_collector = None
_success_metrics = None

def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

def get_success_metrics() -> SuccessMetrics:
    """Get global success metrics instance."""
    global _success_metrics
    if _success_metrics is None:
        _success_metrics = SuccessMetrics(get_metrics_collector())
    return _success_metrics

# Decorator for automatic metrics collection
def track_performance(plugin_name: str = None):
    """Decorator to automatically track function performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                success = False
                raise e
            finally:
                duration = time.time() - start_time
                metrics = get_success_metrics()
                metrics.record_command_execution(
                    command=func.__name__,
                    success=success,
                    response_time=duration,
                    plugin_name=plugin_name
                )
        return wrapper
    return decorator
