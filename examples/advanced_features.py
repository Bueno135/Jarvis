"""
Example of integrating advanced features into Jarvis.
Shows how to use cache, dynamic plugins, NLP, scheduler, learning, and web interface.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import load_config
from core.kernel import Kernel
from core.cache import configure_cache, cache_result
from core.dynamic_plugin_loader import DynamicPluginLoader
from core.advanced_nlp import get_nlp_processor
from core.task_scheduler import get_task_scheduler, scheduled_task, Task, ScheduleType, TaskPriority
from core.continuous_learning import get_continuous_learning
from core.web_interface import create_web_interface

def setup_advanced_features(kernel: Kernel):
    """Setup all advanced features for Jarvis."""
    config = kernel.config
    
    print("🚀 Configuring advanced features...")
    
    # 1. Configure intelligent cache
    print("📦 Setting up intelligent cache...")
    cache_config = config.get("cache", {
        "memory_limit": 100,
        "disk_limit": 1000,
        "default_ttl": 3600,
        "cleanup_interval": 300
    })
    configure_cache(cache_config)
    print("✅ Cache configured")
    
    # 2. Setup dynamic plugin loader
    print("🔌 Setting up dynamic plugin loader...")
    plugin_config = config.get("dynamic_plugins", {
        "plugins_dir": "plugins",
        "hot_reload": True
    })
    dynamic_loader = DynamicPluginLoader(plugin_config)
    
    # Load all plugins dynamically
    loaded_count = dynamic_loader.load_all_plugins()
    print(f"✅ Loaded {loaded_count} plugins dynamically")
    
    # 3. Setup advanced NLP
    print("🧠 Setting up advanced NLP...")
    nlp_config = config.get("nlp", {
        "language": "pt-BR",
        "confidence_threshold": 0.6
    })
    nlp_processor = get_nlp_processor()
    print("✅ NLP processor configured")
    
    # 4. Setup task scheduler
    print("⏰ Setting up task scheduler...")
    scheduler_config = config.get("scheduler", {
        "max_concurrent_tasks": 5,
        "persistence_file": "data/tasks.json"
    })
    scheduler = get_task_scheduler()
    print("✅ Task scheduler configured")
    
    # 5. Setup continuous learning
    print("📚 Setting up continuous learning...")
    learning_config = config.get("learning", {
        "learning_rate": 0.1,
        "min_samples": 5,
        "max_history": 1000
    })
    learning = get_continuous_learning()
    print("✅ Continuous learning configured")
    
    # 6. Setup web interface (optional)
    print("🌐 Setting up web interface...")
    web_config = config.get("web_interface", {
        "host": "localhost",
        "port": 8080,
        "enable_cors": True
    })
    web_interface = create_web_interface(kernel, web_config)
    
    if web_interface:
        print("✅ Web interface configured")
        print(f"   Available at: http://{web_config['host']}:{web_config['port']}")
    else:
        print("⚠️ Web interface not available (install fastapi and uvicorn)")
    
    return {
        "cache": get_cache_instance(),
        "dynamic_loader": dynamic_loader,
        "nlp": nlp_processor,
        "scheduler": scheduler,
        "learning": learning,
        "web_interface": web_interface
    }

def demonstrate_advanced_features(features: dict):
    """Demonstrate the advanced features."""
    print("\n🎯 Demonstrating advanced features...")
    
    # 1. Cache demonstration
    print("\n📦 Cache Demo:")
    cache = features["cache"]
    
    @cache_result(ttl=60, tags=["demo"])
    def expensive_calculation(x: int) -> int:
        """Simulate expensive calculation."""
        import time
        time.sleep(0.1)  # Simulate work
        return x * x
    
    # First call (slow)
    import time
    start = time.time()
    result1 = expensive_calculation(42)
    time1 = time.time() - start
    
    # Second call (fast from cache)
    start = time.time()
    result2 = expensive_calculation(42)
    time2 = time.time() - start
    
    print(f"   First call: {result1} in {time1:.3f}s")
    print(f"   Second call: {result2} in {time2:.3f}s (cached)")
    print(f"   Cache stats: {cache.get_stats()}")
    
    # 2. NLP demonstration
    print("\n🧠 NLP Demo:")
    nlp = features["nlp"]
    
    texts = [
        "abre o notepad",
        "que horas são?",
        "crie um arquivo chamado teste.txt",
        "oi jarvis"
    ]
    
    for text in texts:
        context = nlp.create_context("demo_user", "demo_session")
        intent = nlp.process_text(text, context)
        print(f"   '{text}' -> {intent.name} ({intent.type.value})")
        if intent.entities:
            print(f"     Entities: {[e.text for e in intent.entities]}")
    
    # 3. Task scheduler demonstration
    print("\n⏰ Task Scheduler Demo:")
    scheduler = features["scheduler"]
    
    # Create a simple task
    def demo_task(message: str):
        print(f"🔔 Task executed: {message}")
        return f"Completed: {message}"
    
    # Schedule a task to run in 5 seconds
    task = Task(
        id="demo_task_1",
        name="Demo Task",
        description="A demonstration task",
        function=demo_task,
        args=("Hello from scheduled task!",),
        schedule_type=ScheduleType.ONCE,
        scheduled_at=time.time() + 5,
        priority=TaskPriority.NORMAL
    )
    
    scheduler.add_task(task)
    print(f"   Scheduled task: {task.name}")
    print(f"   Scheduler status: {scheduler.get_scheduler_status()}")
    
    # 4. Learning demonstration
    print("\n📚 Learning Demo:")
    learning = features["learning"]
    
    # Simulate some interactions
    from core.interfaces import CommandContext, CommandResult
    
    for i in range(5):
        context = CommandContext(
            raw_text=f"echo test {i}",
            command_name="Echo",
            params={},
            kernel=None
        )
        
        result = CommandResult(
            success=True,
            message=f"Echo: test {i}"
        )
        
        learning.record_interaction(context, result, 0.1, "demo_user")
    
    print(f"   Recorded {len(learning.learning_data)} interactions")
    print(f"   Suggestions: {len(learning.suggest_improvements())}")
    
    # 5. Dynamic plugins demonstration
    print("\n🔌 Dynamic Plugins Demo:")
    dynamic_loader = features["dynamic_loader"]
    
    plugins_info = dynamic_loader.list_plugins_info()
    print(f"   Loaded plugins: {len(plugins_info)}")
    
    for plugin_info in plugins_info[:3]:  # Show first 3
        print(f"   - {plugin_info['name']}: {plugin_info['description']}")

def create_sample_tasks(scheduler):
    """Create some sample tasks for demonstration."""
    import time
    from datetime import datetime, timedelta
    
    def daily_backup():
        """Sample daily backup task."""
        print("🔔 Running daily backup...")
        return "Backup completed"
    
    def cleanup_temp():
        """Sample cleanup task."""
        print("🔔 Cleaning up temporary files...")
        return "Cleanup completed"
    
    def send_reminder():
        """Sample reminder task."""
        print("🔔 Reminder: Take a break!")
        return "Reminder sent"
    
    # Daily backup at 2 AM
    backup_task = Task(
        id="daily_backup",
        name="Daily Backup",
        description="Perform daily system backup",
        function=daily_backup,
        schedule_type=ScheduleType.DAILY,
        schedule_params={"time": "02:00"},
        priority=TaskPriority.HIGH,
        tags=["backup", "maintenance"]
    )
    
    # Cleanup every 6 hours
    cleanup_task = Task(
        id="cleanup_temp",
        name="Cleanup Temp Files",
        description="Clean up temporary files",
        function=cleanup_temp,
        schedule_type=ScheduleType.INTERVAL,
        schedule_params={"interval": 6, "unit": "hours"},
        priority=TaskPriority.NORMAL,
        tags=["cleanup", "maintenance"]
    )
    
    # Reminder every 2 hours during work hours
    reminder_task = Task(
        id="break_reminder",
        name="Break Reminder",
        description="Remind user to take breaks",
        function=send_reminder,
        schedule_type=ScheduleType.INTERVAL,
        schedule_params={"interval": 2, "unit": "hours"},
        priority=TaskPriority.LOW,
        tags=["reminder", "health"]
    )
    
    # Add tasks to scheduler
    scheduler.add_task(backup_task)
    scheduler.add_task(cleanup_task)
    scheduler.add_task(reminder_task)
    
    print("📋 Created sample tasks:")
    print(f"   - {backup_task.name}: Daily at 2 AM")
    print(f"   - {cleanup_task.name}: Every 6 hours")
    print(f"   - {reminder_task.name}: Every 2 hours")

def main():
    """Main demonstration function."""
    print("🤖 Jarvis Advanced Features Demonstration")
    print("=" * 50)
    
    # Load configuration and initialize kernel
    config = load_config()
    kernel = Kernel(config)
    
    # Setup advanced features
    features = setup_advanced_features(kernel)
    
    # Demonstrate features
    demonstrate_advanced_features(features)
    
    # Create sample tasks
    create_sample_tasks(features["scheduler"])
    
    print("\n🎉 Advanced features demonstration completed!")
    print("\n📖 Features available:")
    print("   📦 Intelligent caching with LRU eviction")
    print("   🔌 Dynamic plugin loading with hot-reload")
    print("   🧠 Advanced NLP with intent recognition")
    print("   ⏰ Task scheduling with dependencies")
    print("   📚 Continuous learning from interactions")
    print("   🌐 Optional web interface")
    
    if features["web_interface"]:
        print(f"\n🌐 Web interface running at: http://{features['web_interface'].host}:{features['web_interface'].port}")
        print("   Open in your browser to control Jarvis!")
    
    print("\n💡 Tips:")
    print("   - Use @cache_result decorator for expensive functions")
    print("   - Dynamic plugins reload automatically when files change")
    print("   - NLP improves command understanding over time")
    print("   - Tasks can be scheduled with various patterns")
    print("   - Learning adapts to user preferences")
    print("   - Web interface provides real-time monitoring")

if __name__ == "__main__":
    import time
    main()
