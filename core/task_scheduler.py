"""
Task scheduling system for Jarvis.
Supports cron-like scheduling, task dependencies, and persistent storage.
"""
import time
import json
import threading
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import logging

class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"

class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class ScheduleType(Enum):
    """Types of scheduling."""
    ONCE = "once"
    INTERVAL = "interval"
    CRON = "cron"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

@dataclass
class Task:
    """Scheduled task definition."""
    id: str
    name: str
    description: str
    function: Callable
    args: tuple = ()
    kwargs: dict = None
    schedule_type: ScheduleType = ScheduleType.ONCE
    schedule_params: Dict[str, Any] = None
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = None
    scheduled_at: Optional[float] = None
    last_run: Optional[float] = None
    next_run: Optional[float] = None
    run_count: int = 0
    max_runs: Optional[int] = None
    timeout: Optional[float] = None
    dependencies: List[str] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.schedule_params is None:
            self.schedule_params = {}
        if self.created_at is None:
            self.created_at = time.time()
        if self.dependencies is None:
            self.dependencies = []
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class TaskResult:
    """Result of task execution."""
    task_id: str
    status: TaskStatus
    started_at: float
    completed_at: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = None

class TaskScheduler:
    """Advanced task scheduler for Jarvis."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger("Jarvis.TaskScheduler")
        
        # Configuration
        self.max_concurrent_tasks = self.config.get("max_concurrent_tasks", 5)
        self.persistence_file = Path(self.config.get("persistence_file", "data/tasks.json"))
        self.persistence_file.parent.mkdir(exist_ok=True)
        
        # Task storage
        self.tasks: Dict[str, Task] = {}
        self.task_results: Dict[str, List[TaskResult]] = {}
        self.running_tasks: Dict[str, threading.Thread] = {}
        
        # Scheduling
        self.scheduler = schedule.Scheduler()
        self.scheduler_thread = None
        self.running = False
        
        # Dependencies tracking
        self.dependency_graph: Dict[str, List[str]] = {}
        
        # Load persisted tasks
        self._load_tasks()
        
        # Start scheduler
        self.start()
        
        self.logger.info("Task scheduler initialized")
    
    def start(self):
        """Start the task scheduler."""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Task scheduler started")
    
    def stop(self):
        """Stop the task scheduler."""
        self.running = False
        
        # Cancel all running tasks
        for task_id, thread in self.running_tasks.items():
            if thread.is_alive():
                self.cancel_task(task_id)
        
        # Wait for scheduler thread
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Task scheduler stopped")
    
    def add_task(self, task: Task) -> bool:
        """Add a new task to the scheduler."""
        with threading.Lock():
            try:
                # Validate task
                if not self._validate_task(task):
                    return False
                
                # Check dependencies
                if not self._check_dependencies(task):
                    return False
                
                # Add to storage
                self.tasks[task.id] = task
                self.task_results[task.id] = []
                
                # Update dependency graph
                self.dependency_graph[task.id] = task.dependencies
                
                # Schedule the task
                self._schedule_task(task)
                
                # Persist
                self._save_tasks()
                
                self.logger.info(f"Task added: {task.name} ({task.id})")
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to add task {task.id}: {e}")
                return False
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the scheduler."""
        with threading.Lock():
            if task_id not in self.tasks:
                self.logger.warning(f"Task not found: {task_id}")
                return False
            
            task = self.tasks[task_id]
            
            # Cancel if running
            if task.status == TaskStatus.RUNNING:
                self.cancel_task(task_id)
            
            # Remove from scheduler
            self._unschedule_task(task_id)
            
            # Remove from storage
            del self.tasks[task_id]
            if task_id in self.task_results:
                del self.task_results[task_id]
            
            # Update dependency graph
            if task_id in self.dependency_graph:
                del self.dependency_graph[task_id]
            
            # Remove from other tasks' dependencies
            for other_task in self.tasks.values():
                other_task.dependencies = [d for d in other_task.dependencies if d != task_id]
            
            # Persist
            self._save_tasks()
            
            self.logger.info(f"Task removed: {task_id}")
            return True
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running or scheduled task."""
        with threading.Lock():
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            
            if task.status == TaskStatus.RUNNING:
                # Cancel running thread (note: this is cooperative cancellation)
                if task_id in self.running_tasks:
                    thread = self.running_tasks[task_id]
                    # In practice, you'd need to implement cancellation flags in your tasks
                    task.status = TaskStatus.CANCELLED
                    del self.running_tasks[task_id]
            
            # Remove from scheduler
            self._unschedule_task(task_id)
            
            task.status = TaskStatus.CANCELLED
            
            # Record result
            result = TaskResult(
                task_id=task_id,
                status=TaskStatus.CANCELLED,
                started_at=time.time(),
                completed_at=time.time()
            )
            self.task_results[task_id].append(result)
            
            self.logger.info(f"Task cancelled: {task_id}")
            return True
    
    def run_task_now(self, task_id: str) -> bool:
        """Run a task immediately, ignoring schedule."""
        with threading.Lock():
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            
            if task.status == TaskStatus.RUNNING:
                self.logger.warning(f"Task already running: {task_id}")
                return False
            
            # Execute in background thread
            thread = threading.Thread(
                target=self._execute_task,
                args=(task,),
                daemon=True
            )
            thread.start()
            
            self.running_tasks[task_id] = thread
            
            self.logger.info(f"Task started immediately: {task_id}")
            return True
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def list_tasks(self, status: Optional[TaskStatus] = None, 
                   tags: Optional[List[str]] = None) -> List[Task]:
        """List tasks with optional filtering."""
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if tags:
            tasks = [t for t in tasks if any(tag in t.tags for tag in tags)]
        
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)
    
    def get_task_results(self, task_id: str, limit: int = 10) -> List[TaskResult]:
        """Get task execution results."""
        results = self.task_results.get(task_id, [])
        return results[-limit:] if limit else results
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get scheduler status information."""
        return {
            "running": self.running,
            "total_tasks": len(self.tasks),
            "running_tasks": len(self.running_tasks),
            "pending_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING]),
            "scheduled_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.SCHEDULED]),
            "failed_tasks": len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED]),
            "next_runs": sorted([(t.id, t.next_run) for t in self.tasks.values() if t.next_run], 
                              key=lambda x: x[1])[:5]
        }
    
    def _validate_task(self, task: Task) -> bool:
        """Validate task definition."""
        if not task.name or not task.id:
            self.logger.error("Task must have name and id")
            return False
        
        if not callable(task.function):
            self.logger.error("Task function must be callable")
            return False
        
        if task.id in self.tasks:
            self.logger.error(f"Task ID already exists: {task.id}")
            return False
        
        return True
    
    def _check_dependencies(self, task: Task) -> bool:
        """Check if task dependencies exist."""
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                self.logger.error(f"Dependency not found: {dep_id}")
                return False
        
        # Check for circular dependencies
        if self._has_circular_dependency(task.id, task.dependencies):
            self.logger.error(f"Circular dependency detected for task: {task.id}")
            return False
        
        return True
    
    def _has_circular_dependency(self, task_id: str, dependencies: List[str], visited: set = None) -> bool:
        """Check for circular dependencies."""
        if visited is None:
            visited = set()
        
        if task_id in visited:
            return True
        
        visited.add(task_id)
        
        for dep_id in dependencies:
            if dep_id in self.tasks:
                dep_task = self.tasks[dep_id]
                if self._has_circular_dependency(dep_id, dep_task.dependencies, visited.copy()):
                    return True
        
        return False
    
    def _schedule_task(self, task: Task):
        """Schedule a task based on its schedule type."""
        job = None
        
        if task.schedule_type == ScheduleType.ONCE:
            if task.scheduled_at:
                delay = task.scheduled_at - time.time()
                if delay > 0:
                    job = self.scheduler.schedule_in(delay, self._execute_task, task)
                else:
                    # Run immediately if time has passed
                    self.run_task_now(task.id)
                    return
        
        elif task.schedule_type == ScheduleType.INTERVAL:
            interval = task.schedule_params.get("interval", 60)  # Default 1 minute
            unit = task.schedule_params.get("unit", "seconds")
            
            if unit == "minutes":
                interval *= 60
            elif unit == "hours":
                interval *= 3600
            elif unit == "days":
                interval *= 86400
            
            job = self.scheduler.schedule_every(interval, self._execute_task, task)
        
        elif task.schedule_type == ScheduleType.CRON:
            # Simplified cron support (you might want to use a proper cron parser)
            cron_expr = task.schedule_params.get("cron", "0 * * * *")
            # This would need a proper cron parser implementation
            self.logger.warning(f"Cron scheduling not fully implemented: {cron_expr}")
        
        elif task.schedule_type == ScheduleType.DAILY:
            time_str = task.schedule_params.get("time", "09:00")
            job = self.scheduler.schedule_daily(time_str, self._execute_task, task)
        
        elif task.schedule_type == ScheduleType.WEEKLY:
            day = task.schedule_params.get("day", "monday")
            time_str = task.schedule_params.get("time", "09:00")
            job = self.scheduler.schedule_weekly(day, time_str, self._execute_task, task)
        
        if job:
            task.status = TaskStatus.SCHEDULED
            task.next_run = time.time() + 60  # Approximate next run
            self.logger.info(f"Task scheduled: {task.id}")
    
    def _unschedule_task(self, task_id: str):
        """Remove task from scheduler."""
        # Note: The schedule library doesn't provide direct job removal
        # This is a simplified implementation
        for job in self.scheduler.jobs:
            if hasattr(job, 'task') and job.task.id == task_id:
                self.scheduler.cancel_job(job)
                break
    
    def _execute_task(self, task: Task):
        """Execute a task."""
        with threading.Lock():
            if task.status == TaskStatus.CANCELLED:
                return
            
            task.status = TaskStatus.RUNNING
            task.last_run = time.time()
            task.run_count += 1
            
            # Check max runs
            if task.max_runs and task.run_count >= task.max_runs:
                task.status = TaskStatus.COMPLETED
                self._unschedule_task(task.id)
            
            # Create result record
            result = TaskResult(
                task_id=task.id,
                status=TaskStatus.RUNNING,
                started_at=time.time()
            )
            
            try:
                # Execute the task
                start_time = time.time()
                task_result = task.function(*task.args, **task.kwargs)
                execution_time = time.time() - start_time
                
                # Update result
                result.status = TaskStatus.COMPLETED
                result.result = task_result
                result.completed_at = time.time()
                result.execution_time = execution_time
                
                task.status = TaskStatus.COMPLETED if task.schedule_type == ScheduleType.ONCE else TaskStatus.SCHEDULED
                
                self.logger.info(f"Task completed: {task.id} in {execution_time:.2f}s")
                
            except Exception as e:
                # Handle task failure
                result.status = TaskStatus.FAILED
                result.error = str(e)
                result.completed_at = time.time()
                
                task.status = TaskStatus.FAILED
                
                self.logger.error(f"Task failed: {task.id} - {e}")
            
            finally:
                # Record result
                self.task_results[task.id].append(result)
                
                # Clean up running tasks
                if task.id in self.running_tasks:
                    del self.running_tasks[task.id]
                
                # Update next run for recurring tasks
                if task.status == TaskStatus.SCHEDULED:
                    self._update_next_run(task)
                
                # Persist
                self._save_tasks()
    
    def _update_next_run(self, task: Task):
        """Update next run time for recurring tasks."""
        if task.schedule_type == ScheduleType.INTERVAL:
            interval = task.schedule_params.get("interval", 60)
            unit = task.schedule_params.get("unit", "seconds")
            
            if unit == "minutes":
                interval *= 60
            elif unit == "hours":
                interval *= 3600
            elif unit == "days":
                interval *= 86400
            
            task.next_run = task.last_run + interval
        
        elif task.schedule_type == ScheduleType.DAILY:
            # Calculate next day at specified time
            time_str = task.schedule_params.get("time", "09:00")
            hour, minute = map(int, time_str.split(":"))
            
            tomorrow = datetime.now() + timedelta(days=1)
            next_run = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            task.next_run = next_run.timestamp()
    
    def _run_scheduler(self):
        """Main scheduler loop."""
        while self.running:
            try:
                self.scheduler.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(5)
    
    def _save_tasks(self):
        """Save tasks to persistent storage."""
        try:
            # Convert tasks to serializable format
            serializable_tasks = {}
            for task_id, task in self.tasks.items():
                task_data = asdict(task)
                # Remove non-serializable function
                task_data.pop('function', None)
                serializable_tasks[task_id] = task_data
            
            # Convert results to serializable format
            serializable_results = {}
            for task_id, results in self.task_results.items():
                serializable_results[task_id] = [asdict(r) for r in results]
            
            data = {
                "tasks": serializable_tasks,
                "results": serializable_results,
                "dependency_graph": self.dependency_graph
            }
            
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Failed to save tasks: {e}")
    
    def _load_tasks(self):
        """Load tasks from persistent storage."""
        if not self.persistence_file.exists():
            return
        
        try:
            with open(self.persistence_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Note: Functions cannot be serialized, so loaded tasks will need
            # to have their functions re-bound by the application
            
            self.logger.info(f"Loaded {len(data.get('tasks', {}))} tasks from storage")
            
        except Exception as e:
            self.logger.error(f"Failed to load tasks: {e}")

# Decorator for easy task creation
def scheduled_task(schedule_type: ScheduleType = ScheduleType.ONCE, 
                  schedule_params: Dict[str, Any] = None,
                  priority: TaskPriority = TaskPriority.NORMAL,
                  tags: List[str] = None):
    """Decorator to easily create scheduled tasks."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This would be called to create the task
            scheduler = get_task_scheduler()
            
            task = Task(
                id=f"{func.__name__}_{int(time.time())}",
                name=func.__name__,
                description=func.__doc__ or f"Scheduled task: {func.__name__}",
                function=func,
                args=args,
                kwargs=kwargs,
                schedule_type=schedule_type,
                schedule_params=schedule_params or {},
                priority=priority,
                tags=tags or []
            )
            
            scheduler.add_task(task)
            return task
        
        return wrapper
    return decorator

# Global scheduler instance
_task_scheduler = None

def get_task_scheduler() -> TaskScheduler:
    """Get global task scheduler instance."""
    global _task_scheduler
    if _task_scheduler is None:
        _task_scheduler = TaskScheduler()
    return _task_scheduler

def configure_scheduler(config: Dict[str, Any]):
    """Configure global task scheduler."""
    global _task_scheduler
    _task_scheduler = TaskScheduler(config)
