"""
Jarvis Performance Benchmark Suite
Comprehensive performance testing and analysis.
"""
import sys
import time
import json
import statistics
import threading
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import psutil
import tracemalloc

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import load_config
from core.kernel import Kernel
from core.cache import get_cache_instance
from core.memory.short_term import ShortTermMemory
from core.memory.long_term import LongTermMemory
from core.plugin_loader import PluginLoader
from core.advanced_nlp import get_nlp_processor
from core.task_scheduler import get_task_scheduler

@dataclass
class BenchmarkResult:
    """Result of a benchmark test."""
    name: str
    category: str
    duration: float
    operations: int
    ops_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success_rate: float
    errors: List[str]
    metadata: Dict[str, Any]

@dataclass
class PerformanceReport:
    """Comprehensive performance report."""
    timestamp: str
    system_info: Dict[str, Any]
    benchmarks: List[BenchmarkResult]
    summary: Dict[str, Any]
    recommendations: List[str]

class JarvisBenchmark:
    """Comprehensive performance benchmarking suite."""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or "config/config.yaml"
        self.config = load_config()
        self.kernel = Kernel(self.config)
        self.results = []
        self.start_time = None
        
        # Performance tracking
        tracemalloc.start()
        self.initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
    def run_all_benchmarks(self) -> PerformanceReport:
        """Run all benchmark tests."""
        print("🚀 Starting Jarvis Performance Benchmark Suite")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # System information
        system_info = self._get_system_info()
        
        # Run benchmark categories
        benchmark_categories = [
            ("Kernel Performance", self._benchmark_kernel),
            ("Plugin System", self._benchmark_plugins),
            ("Memory System", self._benchmark_memory),
            ("Cache Performance", self._benchmark_cache),
            ("NLP Processing", self._benchmark_nlp),
            ("Task Scheduling", self._benchmark_scheduler),
            ("Concurrent Operations", self._benchmark_concurrent),
            ("Resource Usage", self._benchmark_resources)
        ]
        
        for category_name, benchmark_func in benchmark_categories:
            print(f"\n📊 Running {category_name} benchmarks...")
            try:
                benchmark_func()
            except Exception as e:
                print(f"❌ {category_name} benchmark failed: {e}")
        
        # Generate report
        report = self._generate_report(system_info)
        
        # Print summary
        self._print_summary(report)
        
        # Save report
        self._save_report(report)
        
        return report
    
    def _benchmark_kernel(self):
        """Benchmark kernel operations."""
        commands = [
            "echo hello world",
            "what time is it",
            "help",
            "status",
            "echo performance test"
        ]
        
        # Single command performance
        durations = []
        errors = []
        
        for _ in range(100):
            start = time.time()
            try:
                result = self.kernel.dispatch(commands[0])
                if result.success:
                    durations.append(time.time() - start)
                else:
                    errors.append(result.message)
            except Exception as e:
                errors.append(str(e))
        
        self._add_result(
            name="Kernel Command Dispatch",
            category="Kernel Performance",
            durations=durations,
            operations=len(durations),
            errors=errors
        )
        
        # Multiple commands throughput
        start = time.time()
        operations = 0
        errors = []
        
        for _ in range(50):
            for cmd in commands:
                try:
                    result = self.kernel.dispatch(cmd)
                    if result.success:
                        operations += 1
                    else:
                        errors.append(result.message)
                except Exception as e:
                    errors.append(str(e))
        
        duration = time.time() - start
        
        self._add_result(
            name="Kernel Throughput",
            category="Kernel Performance",
            durations=[duration],
            operations=operations,
            errors=errors,
            metadata={"commands_tested": len(commands)}
        )
    
    def _benchmark_plugins(self):
        """Benchmark plugin system."""
        loader = PluginLoader()
        plugins = loader.discover_and_load()
        
        if not plugins:
            print("⚠️ No plugins found for benchmarking")
            return
        
        # Plugin loading time
        durations = []
        errors = []
        
        for _ in range(10):
            start = time.time()
            try:
                loaded_plugins = loader.discover_and_load()
                durations.append(time.time() - start)
            except Exception as e:
                errors.append(str(e))
        
        self._add_result(
            name="Plugin Loading",
            category="Plugin System",
            durations=durations,
            operations=len(durations),
            errors=errors,
            metadata={"plugins_loaded": len(plugins)}
        )
        
        # Plugin execution performance
        plugin = plugins[0] if plugins else None
        if plugin:
            durations = []
            errors = []
            
            from core.interfaces import CommandContext
            
            for _ in range(100):
                ctx = CommandContext(
                    raw_text="test command",
                    command_name=plugin.name(),
                    params={},
                    kernel=self.kernel
                )
                
                start = time.time()
                try:
                    result = plugin.execute(ctx)
                    if result.success:
                        durations.append(time.time() - start)
                    else:
                        errors.append(result.message)
                except Exception as e:
                    errors.append(str(e))
            
            self._add_result(
                name="Plugin Execution",
                category="Plugin System",
                durations=durations,
                operations=len(durations),
                errors=errors,
                metadata={"plugin_name": plugin.name()}
            )
    
    def _benchmark_memory(self):
        """Benchmark memory system."""
        # Short-term memory
        stm = ShortTermMemory(max_entries=100)
        
        # Memory write performance
        durations = []
        errors = []
        
        from core.interfaces import MemoryEntry
        
        for i in range(100):
            entry = MemoryEntry(
                id=f"test_{i}",
                content=f"Test content {i}",
                metadata={"type": "test"},
                timestamp=time.time(),
                entry_type="session"
            )
            
            start = time.time()
            try:
                stm.store(entry)
                durations.append(time.time() - start)
            except Exception as e:
                errors.append(str(e))
        
        self._add_result(
            name="Short-term Memory Write",
            category="Memory System",
            durations=durations,
            operations=len(durations),
            errors=errors
        )
        
        # Memory read performance
        durations = []
        errors = []
        
        for i in range(100):
            start = time.time()
            try:
                results = stm.query(f"test {i}", k=5)
                durations.append(time.time() - start)
            except Exception as e:
                errors.append(str(e))
        
        self._add_result(
            name="Short-term Memory Read",
            category="Memory System",
            durations=durations,
            operations=len(durations),
            errors=errors
        )
        
        # Long-term memory (if available)
        try:
            ltm = LongTermMemory("benchmark_memory")
            
            # Write performance
            durations = []
            errors = []
            
            for i in range(50):
                entry = MemoryEntry(
                    id=f"ltm_test_{i}",
                    content=f"Long-term test content {i}",
                    metadata={"type": "test", "persistent": True},
                    timestamp=time.time(),
                    entry_type="persistent"
                )
                
                start = time.time()
                try:
                    ltm.store(entry)
                    durations.append(time.time() - start)
                except Exception as e:
                    errors.append(str(e))
            
            self._add_result(
                name="Long-term Memory Write",
                category="Memory System",
                durations=durations,
                operations=len(durations),
                errors=errors
            )
            
        except Exception as e:
            print(f"⚠️ Long-term memory benchmark skipped: {e}")
    
    def _benchmark_cache(self):
        """Benchmark cache system."""
        cache = get_cache_instance()
        
        # Cache write performance
        durations = []
        errors = []
        
        for i in range(100):
            start = time.time()
            try:
                cache.set(f"key_{i}", f"value_{i}", ttl=300)
                durations.append(time.time() - start)
            except Exception as e:
                errors.append(str(e))
        
        self._add_result(
            name="Cache Write",
            category="Cache Performance",
            durations=durations,
            operations=len(durations),
            errors=errors
        )
        
        # Cache read performance (hit)
        durations = []
        errors = []
        
        # Pre-populate cache
        for i in range(50):
            cache.set(f"hit_key_{i}", f"hit_value_{i}")
        
        for i in range(50):
            start = time.time()
            try:
                result = cache.get(f"hit_key_{i}")
                durations.append(time.time() - start)
                if result is None:
                    errors.append(f"Cache miss for hit_key_{i}")
            except Exception as e:
                errors.append(str(e))
        
        self._add_result(
            name="Cache Read (Hit)",
            category="Cache Performance",
            durations=durations,
            operations=len(durations),
            errors=errors
        )
        
        # Cache read performance (miss)
        durations = []
        errors = []
        
        for i in range(50):
            start = time.time()
            try:
                result = cache.get(f"miss_key_{i}")
                durations.append(time.time() - start)
                if result is not None:
                    errors.append(f"Unexpected hit for miss_key_{i}")
            except Exception as e:
                errors.append(str(e))
        
        self._add_result(
            name="Cache Read (Miss)",
            category="Cache Performance",
            durations=durations,
            operations=len(durations),
            errors=errors
        )
    
    def _benchmark_nlp(self):
        """Benchmark NLP processing."""
        try:
            nlp = get_nlp_processor()
            
            test_texts = [
                "abre o notepad",
                "que horas são agora",
                "crie um arquivo chamado teste.txt",
                "olá jarvis",
                "mostre o clima hoje",
                "calcule 2 + 2",
                "desligue o computador",
                "toque uma música",
                "envie um email",
                "abra o navegador"
            ]
            
            # Text processing performance
            durations = []
            errors = []
            
            for _ in range(50):
                text = test_texts[_ % len(test_texts)]
                context = nlp.create_context("benchmark_user", "benchmark_session")
                
                start = time.time()
                try:
                    intent = nlp.process_text(text, context)
                    durations.append(time.time() - start)
                except Exception as e:
                    errors.append(str(e))
            
            self._add_result(
                name="NLP Text Processing",
                category="NLP Processing",
                durations=durations,
                operations=len(durations),
                errors=errors,
                metadata={"texts_tested": len(test_texts)}
            )
            
        except Exception as e:
            print(f"⚠️ NLP benchmark skipped: {e}")
    
    def _benchmark_scheduler(self):
        """Benchmark task scheduling."""
        try:
            scheduler = get_task_scheduler()
            
            # Task creation performance
            durations = []
            errors = []
            
            def dummy_task():
                return "completed"
            
            for i in range(50):
                from core.task_scheduler import Task, ScheduleType, TaskPriority
                
                task = Task(
                    id=f"benchmark_task_{i}",
                    name=f"Benchmark Task {i}",
                    description="Performance test task",
                    function=dummy_task,
                    schedule_type=ScheduleType.ONCE,
                    priority=TaskPriority.NORMAL
                )
                
                start = time.time()
                try:
                    success = scheduler.add_task(task)
                    durations.append(time.time() - start)
                    if not success:
                        errors.append(f"Failed to add task {i}")
                except Exception as e:
                    errors.append(str(e))
            
            self._add_result(
                name="Task Creation",
                category="Task Scheduling",
                durations=durations,
                operations=len(durations),
                errors=errors
            )
            
            # Task execution performance
            durations = []
            errors = []
            
            for i in range(20):
                task_id = f"benchmark_task_{i}"
                start = time.time()
                try:
                    success = scheduler.run_task_now(task_id)
                    durations.append(time.time() - start)
                    if not success:
                        errors.append(f"Failed to run task {i}")
                except Exception as e:
                    errors.append(str(e))
            
            self._add_result(
                name="Task Execution",
                category="Task Scheduling",
                durations=durations,
                operations=len(durations),
                errors=errors
            )
            
        except Exception as e:
            print(f"⚠️ Task scheduler benchmark skipped: {e}")
    
    def _benchmark_concurrent(self):
        """Benchmark concurrent operations."""
        # Concurrent command dispatch
        durations = []
        errors = []
        
        def dispatch_command():
            start = time.time()
            try:
                result = self.kernel.dispatch("echo concurrent test")
                return time.time() - start, result.success
            except Exception as e:
                return time.time() - start, False
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(dispatch_command) for _ in range(50)]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    duration, success = future.result()
                    if success:
                        durations.append(duration)
                    else:
                        errors.append("Command failed")
                except Exception as e:
                    errors.append(str(e))
        
        self._add_result(
            name="Concurrent Commands",
            category="Concurrent Operations",
            durations=durations,
            operations=len(durations),
            errors=errors,
            metadata={"max_workers": 10}
        )
    
    def _benchmark_resources(self):
        """Benchmark resource usage."""
        # Memory usage under load
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Create load
        cache = get_cache_instance()
        
        for i in range(1000):
            cache.set(f"load_key_{i}", f"load_value_{i}" * 100)  # Larger values
        
        peak_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_increase = peak_memory - initial_memory
        
        # CPU usage under load
        cpu_samples = []
        
        for _ in range(10):
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_samples.append(cpu_percent)
        
        avg_cpu = statistics.mean(cpu_samples)
        
        self._add_result(
            name="Memory Usage Under Load",
            category="Resource Usage",
            durations=[0.1],  # Not time-based
            operations=1000,
            errors=[],
            metadata={
                "initial_memory_mb": initial_memory,
                "peak_memory_mb": peak_memory,
                "memory_increase_mb": memory_increase
            }
        )
        
        self._add_result(
            name="CPU Usage Under Load",
            category="Resource Usage",
            durations=[0.1],  # Not time-based
            operations=len(cpu_samples),
            errors=[],
            metadata={
                "avg_cpu_percent": avg_cpu,
                "max_cpu_percent": max(cpu_samples)
            }
        )
    
    def _add_result(self, name: str, category: str, durations: List[float], 
                   operations: int, errors: List[str], metadata: Dict[str, Any] = None):
        """Add a benchmark result."""
        if not durations:
            return
        
        avg_duration = statistics.mean(durations)
        ops_per_second = operations / sum(durations) if durations else 0
        
        # Get current resource usage
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        success_rate = (operations - len(errors)) / operations if operations > 0 else 0
        
        result = BenchmarkResult(
            name=name,
            category=category,
            duration=avg_duration,
            operations=operations,
            ops_per_second=ops_per_second,
            memory_usage_mb=memory_mb,
            cpu_usage_percent=cpu_percent,
            success_rate=success_rate,
            errors=errors[:5],  # Limit errors
            metadata=metadata or {}
        )
        
        self.results.append(result)
        
        # Print immediate result
        status = "✅" if success_rate >= 0.95 else "⚠️" if success_rate >= 0.8 else "❌"
        print(f"  {status} {name}: {ops_per_second:.2f} ops/sec, {success_rate:.1%} success")
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        cpu_info = {
            "brand": psutil.cpu_freq().brand if psutil.cpu_freq() else "Unknown",
            "cores": psutil.cpu_count(),
            "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else 0
        }
        
        memory_info = psutil.virtual_memory()
        
        return {
            "platform": sys.platform,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "cpu": cpu_info,
            "memory": {
                "total_gb": memory_info.total / (1024**3),
                "available_gb": memory_info.available / (1024**3)
            },
            "disk": {
                "total_gb": psutil.disk_usage('/').total / (1024**3),
                "free_gb": psutil.disk_usage('/').free / (1024**3)
            }
        }
    
    def _generate_report(self, system_info: Dict[str, Any]) -> PerformanceReport:
        """Generate comprehensive performance report."""
        # Calculate summary statistics
        total_operations = sum(r.operations for r in self.results)
        total_errors = sum(len(r.errors) for r in self.results)
        overall_success_rate = (total_operations - total_errors) / total_operations if total_operations > 0 else 0
        
        # Performance categories
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        # Recommendations
        recommendations = self._generate_recommendations()
        
        return PerformanceReport(
            timestamp=datetime.now().isoformat(),
            system_info=system_info,
            benchmarks=self.results,
            summary={
                "total_duration": time.time() - self.start_time,
                "total_operations": total_operations,
                "overall_success_rate": overall_success_rate,
                "categories": {cat: len(results) for cat, results in categories.items()},
                "avg_ops_per_second": statistics.mean([r.ops_per_second for r in self.results]),
                "peak_memory_mb": max(r.memory_usage_mb for r in self.results),
                "avg_cpu_percent": statistics.mean([r.cpu_usage_percent for r in self.results])
            },
            recommendations=recommendations
        )
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        # Analyze results
        for result in self.results:
            if result.ops_per_second < 10:
                recommendations.append(f"⚠️ {result.name} performance is low ({result.ops_per_second:.2f} ops/sec)")
            elif result.ops_per_second < 50:
                recommendations.append(f"💡 Consider optimizing {result.name} ({result.ops_per_second:.2f} ops/sec)")
            
            if result.success_rate < 0.95:
                recommendations.append(f"🔧 {result.name} has {result.success_rate:.1%} success rate")
            
            if result.memory_usage_mb > 500:
                recommendations.append(f"💾 {result.name} uses high memory ({result.memory_usage_mb:.1f} MB)")
        
        # General recommendations
        avg_ops_per_sec = statistics.mean([r.ops_per_second for r in self.results])
        if avg_ops_per_sec < 50:
            recommendations.append("🚀 Consider enabling caching for better performance")
        
        if len(recommendations) == 0:
            recommendations.append("✅ All performance metrics look good!")
        
        return recommendations
    
    def _print_summary(self, report: PerformanceReport):
        """Print performance summary."""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 60)
        
        print(f"⏱️  Total Duration: {report.summary['total_duration']:.2f}s")
        print(f"🔢 Total Operations: {report.summary['total_operations']}")
        print(f"✅ Overall Success Rate: {report.summary['overall_success_rate']:.1%}")
        print(f"⚡ Average Ops/Sec: {report.summary['avg_ops_per_second']:.2f}")
        print(f"💾 Peak Memory: {report.summary['peak_memory_mb']:.1f} MB")
        print(f"🖥️  Average CPU: {report.summary['avg_cpu_percent']:.1f}%")
        
        print(f"\n📈 Performance by Category:")
        for category, count in report.summary['categories'].items():
            category_results = [r for r in report.benchmarks if r.category == category]
            avg_ops = statistics.mean([r.ops_per_second for r in category_results])
            print(f"  {category}: {count} tests, {avg_ops:.2f} avg ops/sec")
        
        print(f"\n💡 Recommendations:")
        for rec in report.recommendations:
            print(f"  {rec}")
    
    def _save_report(self, report: PerformanceReport):
        """Save performance report to file."""
        # Create reports directory
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        
        # Save JSON report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = reports_dir / f"benchmark_report_{timestamp}.json"
        
        # Convert dataclasses to dict for JSON serialization
        report_dict = asdict(report)
        
        with open(json_file, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        print(f"\n📄 Report saved to: {json_file}")
        
        # Save summary text report
        text_file = reports_dir / f"benchmark_summary_{timestamp}.txt"
        with open(text_file, 'w') as f:
            f.write(f"Jarvis Performance Benchmark Report\n")
            f.write(f"Generated: {report.timestamp}\n")
            f.write(f"System: {report.system_info['platform']} - Python {report.system_info['python_version']}\n")
            f.write(f"\nSummary:\n")
            for key, value in report.summary.items():
                f.write(f"  {key}: {value}\n")
            f.write(f"\nRecommendations:\n")
            for rec in report.recommendations:
                f.write(f"  {rec}\n")
        
        print(f"📄 Summary saved to: {text_file}")

def run_specific_benchmark(category: str = None):
    """Run specific benchmark category."""
    benchmark = JarvisBenchmark()
    
    if category == "kernel":
        benchmark._benchmark_kernel()
    elif category == "plugins":
        benchmark._benchmark_plugins()
    elif category == "memory":
        benchmark._benchmark_memory()
    elif category == "cache":
        benchmark._benchmark_cache()
    elif category == "nlp":
        benchmark._benchmark_nlp()
    elif category == "scheduler":
        benchmark._benchmark_scheduler()
    elif category == "concurrent":
        benchmark._benchmark_concurrent()
    elif category == "resources":
        benchmark._benchmark_resources()
    else:
        print(f"Unknown category: {category}")
        print("Available categories: kernel, plugins, memory, cache, nlp, scheduler, concurrent, resources")
        return
    
    # Print results for this category
    category_results = [r for r in benchmark.results if r.category.replace(" ", "_").lower() == category.lower()]
    for result in category_results:
        print(f"{result.name}: {result.ops_per_second:.2f} ops/sec, {result.success_rate:.1%} success")

def main():
    """Main benchmark execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Jarvis Performance Benchmark")
    parser.add_argument("--category", help="Run specific benchmark category")
    parser.add_argument("--config", help="Configuration file path")
    
    args = parser.parse_args()
    
    if args.category:
        run_specific_benchmark(args.category)
    else:
        benchmark = JarvisBenchmark(args.config)
        report = benchmark.run_all_benchmarks()
        
        # Return exit code based on performance
        if report.summary['overall_success_rate'] < 0.8:
            sys.exit(1)
        elif report.summary['avg_ops_per_second'] < 10:
            sys.exit(1)
        else:
            sys.exit(0)

if __name__ == "__main__":
    main()
