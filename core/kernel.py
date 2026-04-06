import logging
import re
from enum import Enum
from typing import Dict, List, Callable, Any, Optional
from .interfaces import PluginBase, CommandResult, CommandContext, MemoryEntry, TaskPlan, TaskStep, TaskStatus
from .logger import setup_logger
import time
import uuid


class SystemState(Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    EXECUTING = "EXECUTING"
    ERROR = "ERROR"

class Kernel:
    """
    The heart of the Jarvis system.
    Acts as:
    1. Service Container
    2. Event Dispatcher
    3. State Manager
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logger("Jarvis.Kernel", config)
        self.services: Dict[str, Any] = {}
        self.events: Dict[str, List[Callable]] = {}
        self.state = SystemState.IDLE
        self.plugins: Dict[str, PluginBase] = {}
        
        # Initialize Security Manager
        from .security import SecurityManager
        self.security_manager = SecurityManager(config)
        self.register_service("security", self.security_manager)
        
        # Initialize Plugin Loader
        from .plugin_loader import PluginLoader
        self.plugin_loader = PluginLoader(config=config)
        self.load_plugins()

        # Initialize Memory Services
        try:
            from .memory import ShortTermMemory, LongTermMemory
            memory_config = config.get("memory", {})

            self.short_memory = ShortTermMemory(
                max_entries=memory_config.get("max_entries", 50)
            )
            self.register_service("short_memory", self.short_memory)

            self.long_memory = LongTermMemory(
                persist_path=memory_config.get("persist_path", "data/memory")
            )
            self.register_service("long_memory", self.long_memory)
            self.logger.info("Memory services initialized.")
        except Exception as e:
            self.logger.error(f"Failed to load Memory services: {e}")
            self.short_memory = None
            self.long_memory = None

        # Initialize BrowserService (lazy — created on first use)
        self._browser_service = None
        web_config = config.get("web", {})
        self._web_headless = web_config.get("headless", True)
        self._web_timeout = web_config.get("timeout", 30000)
        self.register_service("browser", self._get_browser_service)

        # Initialize TTS
        try:
            from .tts import EdgeTTSService
            self.tts = EdgeTTSService(config)
            self.register_service("tts", self.tts)
        except Exception as e:
            self.logger.error(f"Failed to load TTS: {e}")
            self.tts = None

        self.logger.info("Kernel initialized.")

    def load_plugins(self):
        """
        Loads plugins using the PluginLoader and registers them.
        """
        loaded = self.plugin_loader.discover_and_load()
        for plugin in loaded:
            self.register_plugin(plugin)

    # --- State Management ---
    def set_state(self, new_state: SystemState):
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.logger.info(f"State transition: {old_state.value} -> {new_state.value}")
            self.emit("state_changed", {"old": old_state.value, "new": new_state.value})

    # --- Service Container ---
    def register_service(self, name: str, service: Any):
        self.services[name] = service
        self.logger.debug(f"Service registered: {name}")

    def _get_browser_service(self):
        """Lazily create BrowserService on first access."""
        if self._browser_service is None:
            try:
                from .web.browser_service import BrowserService
                self._browser_service = BrowserService(
                    headless=self._web_headless,
                    timeout=self._web_timeout
                )
                self.logger.info("BrowserService initialized (lazy).")
            except Exception as e:
                self.logger.error(f"Failed to create BrowserService: {e}")
                return None
        return self._browser_service

    def get_service(self, name: str) -> Any:
        svc = self.services.get(name)
        # If the service is a callable (lazy factory), call it
        if callable(svc) and name == "browser":
            return svc()
        return svc

    # --- Event Bus ---
    def subscribe(self, event_name: str, handler: Callable):
        if event_name not in self.events:
            self.events[event_name] = []
        self.events[event_name].append(handler)
        self.logger.debug(f"Subscribed to event: {event_name}")

    def emit(self, event_name: str, payload: Any = None):
        if event_name in self.events:
            for handler in self.events[event_name]:
                try:
                    handler(payload)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event_name}: {e}")

    # --- Plugin Management ---
    def register_plugin(self, plugin: PluginBase):
        if plugin.name() in self.plugins:
            self.logger.warning(f"Plugin {plugin.name()} already registered. Overwriting.")
        
        self.plugins[plugin.name()] = plugin
        self.logger.info(f"Plugin registered: {plugin.name()} with patterns: {plugin.patterns()}")

    def speak(self, text: str):
        """
        Speak the given text using the registered TTS service.
        """
        if self.tts:
            self.tts.speak(text)
        else:
            self.logger.warning("TTS not available.")

    def _store_in_memory(self, text: str, result: CommandResult):
        """Store a command and its result in short-term memory."""
        if self.short_memory:
            try:
                entry = MemoryEntry(
                    id=str(uuid.uuid4()),
                    content=f"Command: {text} | Result: {result.message}",
                    metadata={"success": result.success, "data": result.data},
                    timestamp=time.time(),
                )
                self.short_memory.store(entry)
            except Exception as e:
                self.logger.error(f"Failed to store in memory: {e}")

    def execute_plan(self, plan: TaskPlan) -> TaskPlan:
        """
        Execute a multi-step TaskPlan sequentially.
        Updates step statuses and emits events as execution progresses.
        Returns the updated plan.
        """
        # Set plan status to RUNNING
        plan.status = TaskStatus.RUNNING
        self.emit("plan_started", {"goal": plan.goal, "total_steps": len(plan.steps)})
        self.logger.info(f"Starting plan execution: {plan.goal} with {len(plan.steps)} steps")

        # Iterate through each step in the plan
        for step in plan.steps:
            # Set step status to RUNNING
            step.status = TaskStatus.RUNNING
            self.emit("step_started", {
                "step_id": step.id,
                "description": step.description,
                "plugin_name": step.plugin_name,
                "step_index": plan.current_step_index
            })
            self.logger.info(f"Executing step {plan.current_step_index}: {step.description}")

            # Find the plugin by name
            plugin = self.plugins.get(step.plugin_name)
            if not plugin:
                self.logger.error(f"Plugin not found: {step.plugin_name}")
                step.status = TaskStatus.FAILED
                plan.status = TaskStatus.FAILED
                self.emit("step_failed", {
                    "step_id": step.id,
                    "description": step.description,
                    "reason": f"Plugin not found: {step.plugin_name}"
                })
                break

            # Create CommandContext for this step
            try:
                ctx = CommandContext(
                    raw_text=step.description,
                    command_name=step.plugin_name,
                    params=step.params,
                    kernel=self
                )

                # Execute the plugin
                result = plugin.execute(ctx)
                step.result = result

                # Check if execution was successful
                if result.success:
                    step.status = TaskStatus.DONE
                    self.emit("step_completed", {
                        "step_id": step.id,
                        "description": step.description,
                        "result": result.message
                    })
                    self.logger.info(f"Step {plan.current_step_index} completed successfully")
                else:
                    step.status = TaskStatus.FAILED
                    plan.status = TaskStatus.FAILED
                    self.emit("step_failed", {
                        "step_id": step.id,
                        "description": step.description,
                        "reason": result.message
                    })
                    self.logger.error(f"Step {plan.current_step_index} failed: {result.message}")
                    break

                # Store intermediate result in memory
                self._store_in_memory(step.description, result)

            except Exception as e:
                self.logger.error(f"Exception during step execution: {e}")
                step.status = TaskStatus.FAILED
                plan.status = TaskStatus.FAILED
                self.emit("step_failed", {
                    "step_id": step.id,
                    "description": step.description,
                    "reason": str(e)
                })
                break

            # Update plan's current step index
            plan.current_step_index += 1

        # If all steps completed successfully, set plan status to DONE
        if all(s.status == TaskStatus.DONE for s in plan.steps):
            plan.status = TaskStatus.DONE
            self.emit("plan_completed", {
                "goal": plan.goal,
                "total_steps": len(plan.steps)
            })
            self.logger.info(f"Plan completed successfully: {plan.goal}")

        return plan

    def _handle_complex_task(self, text: str) -> CommandResult:
        """
        Handle a complex multi-step task by planning and executing it.
        """
        try:
            from .task_planner import TaskPlanner
            planner = TaskPlanner(self)
            available = list(self.plugins.keys())

            self.speak("Planejando a tarefa...")
            plan = planner.plan(text, available)

            if not plan.steps:
                return CommandResult(False, "Could not create a plan for this task.")

            self.logger.info(f"Plan created with {len(plan.steps)} steps")

            # Store plan in memory
            self._store_in_memory(
                f"Plan for: {text}",
                CommandResult(True, f"Plan: {[s.description for s in plan.steps]}")
            )

            # Execute
            self.speak(f"Executando plano com {len(plan.steps)} etapas.")
            result_plan = self.execute_plan(plan)

            if result_plan.status == TaskStatus.DONE:
                self.speak("Tarefa concluída com sucesso.")
                return CommandResult(
                    True,
                    f"Complex task completed: {text}",
                    data={"plan_goal": plan.goal, "steps_completed": len(plan.steps)}
                )
            else:
                failed_steps = [s for s in plan.steps if s.status == TaskStatus.FAILED]
                fail_msg = failed_steps[0].result.message if failed_steps and failed_steps[0].result else "Unknown error"
                self.speak(f"A tarefa falhou na etapa: {failed_steps[0].description if failed_steps else 'desconhecida'}")
                return CommandResult(
                    False,
                    f"Task partially completed. Failed at: {fail_msg}",
                    data={"plan_goal": plan.goal, "completed": plan.current_step_index}
                )
        except Exception as e:
            self.logger.error(f"Complex task handling failed: {e}")
            return CommandResult(False, f"Failed to plan/execute complex task: {e}")

    def _match_pattern(self, pattern: str, text: str) -> bool:
        """
        Match pattern against text using word boundaries.
        Supports both simple keywords and regex patterns.
        """
        text_lower = text.lower()
        pattern_lower = pattern.lower()
        
        # Check if pattern looks like a regex (contains special chars)
        if any(c in pattern for c in r'[](){}.*+?^$|\\'):
            try:
                return bool(re.search(pattern, text, re.IGNORECASE))
            except re.error:
                pass
        
        # Use word boundary matching for simple keywords
        # This prevents "open" from matching "reopen" or "cooperate"
        word_pattern = r'\b' + re.escape(pattern_lower) + r'\b'
        return bool(re.search(word_pattern, text_lower))

    def _find_plugin_for_intent(self, intent: str) -> Optional[PluginBase]:
        """
        Find a plugin that handles a given AI intent.
        First checks if plugin declares the intent, then falls back to name mapping.
        """
        # Check if any plugin declares this intent
        for plugin in self.plugins.values():
            if hasattr(plugin, 'intents') and callable(plugin.intents):
                if intent in plugin.intents():
                    return plugin
        
        # Fallback: built-in intent -> plugin name mapping
        intent_map = {
            "open_app": "OpenApp",
            "create_file": "FileOps",
            "write_text": "FileOps",
            "run_shell": "RunShell"
        }
        
        target_name = intent_map.get(intent)
        if target_name:
            return self.plugins.get(target_name)
        
        return None

    def dispatch(self, text: str) -> CommandResult:
        """
        Main entry point for text commands.
        Finds the matching plugin and executes it.
        """
        self.set_state(SystemState.PROCESSING)
        self.logger.info(f"Dispatching command: {text}")

        # 1. Intent Parsing (Rule-Based First)
        matched_plugin = None
        command_name = ""
        params = {}
        
        # Try to find plugin by pattern (Rule/Keyword/Regex) with word boundary matching
        for name, plugin in self.plugins.items():
            for pattern in plugin.patterns():
                if self._match_pattern(pattern, text):
                    matched_plugin = plugin
                    command_name = plugin.name()
                    self.logger.debug(f"Pattern '{pattern}' matched for plugin {name}")
                    break
            if matched_plugin:
                break
        
        # 2. AI Fallback (If no plugin matched via rules)
        if not matched_plugin:
            self.logger.info("No rule matched. Trying AI Fallback...")
            try:
                # Lazy load resolver if needed
                if not hasattr(self, 'ai_resolver'):
                    from .ai.ai_intent_resolver import AIIntentResolver
                    self.ai_resolver = AIIntentResolver(self)
                
                ai_result = self.ai_resolver.resolve(text)
                
                if ai_result:
                    intent = ai_result.get("intent")
                    if intent == "question":
                        response_text = ai_result.get('response')
                        self.logger.info(f"AI Response: {response_text}")
                        self.speak(response_text)
                        result = CommandResult(True, f"AI: {response_text}")
                        self._store_in_memory(text, result)
                        return result

                    # Multi-step / complex task — delegate to TaskPlanner
                    if intent in ("multi_step", "complex_task"):
                        self.logger.info(f"Complex task detected, invoking TaskPlanner: {text}")
                        return self._handle_complex_task(text)

                    # Find plugin for this intent
                    matched_plugin = self._find_plugin_for_intent(intent)
                    if matched_plugin:
                        command_name = intent
                        params = ai_result.get("parameters", {})
                        self.logger.info(f"AI routed to plugin: {matched_plugin.name()}")

            except Exception as e:
                import traceback
                self.logger.error(f"AI Fallback failed: {e}")
                self.logger.error(traceback.format_exc())

        
        if matched_plugin:
            self.set_state(SystemState.EXECUTING)
            try:
                # Contexto agora pode ter parâmetros vindos da IA
                ctx = CommandContext(
                    raw_text=text,
                    command_name=command_name,
                    params=params, # Passar parametros
                    kernel=self
                )
                
                result = matched_plugin.execute(ctx)
                
                self.logger.info(f"Command executed: {result.message}", extra={
                    "event": "COMMAND_EXECUTED",
                    "command": matched_plugin.name(),
                    "status": "SUCCESS" if result.success else "FAILURE"
                })

                # Store command and result in short-term memory
                self._store_in_memory(text, result)

                self.set_state(SystemState.IDLE)
                return result
                
            except Exception as e:
                self.logger.error(f"Plugin execution failed: {e}")
                self.set_state(SystemState.ERROR)
                self.speak("Ocorreu um erro ao executar o comando.")
                return CommandResult(success=False, message=str(e))
        else:
            self.logger.warning(f"No intent found for: {text}")
            self.set_state(SystemState.IDLE)
            return CommandResult(success=False, message="I didn't understand that command.")
