import logging
from enum import Enum
from typing import Dict, List, Callable, Any
from .interfaces import PluginBase, CommandResult, CommandContext
from .logger import setup_logger

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

    def get_service(self, name: str) -> Any:
        return self.services.get(name)

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
        
        # Tenta encontrar plugin por padrão (Regra/Keyword/Regex)
        for name, plugin in self.plugins.items():
            for pattern in plugin.patterns():
                if pattern in text: 
                    matched_plugin = plugin
                    command_name = plugin.name()
                    break
            if matched_plugin:
                break
        
        # 2. AI Fallback (Se nenhum plugin casou via regra)
        if not matched_plugin:
            self.logger.info("Nenhuma regra casou. Tentando AI Fallback...")
            try:
                # Lazy load do resolver se precisar (ou init no constructor)
                if not hasattr(self, 'ai_resolver'):
                   from .ai.ai_intent_resolver import AIIntentResolver
                   self.ai_resolver = AIIntentResolver(self)
                
                ai_result = self.ai_resolver.resolve(text)
                
                if ai_result:
                    intent = ai_result.get("intent")
                    if intent == "question":
                         response_text = ai_result.get('response')
                         self.logger.info(f"AI Response: {response_text}")
                         self.speak(response_text) # SPEAK THE RESPONSE
                         return CommandResult(True, f"AI: {response_text}")
                    
                    # Mapear Intenção da IA -> Plugin
                    # Precisamos saber qual plugin trata qual intenção.
                    # Por enquanto, assumimos que o nome da intenção == nome comando interno (ex: open_app)
                    # Ou fazemos um mapa reverso.
                    
                    # Para MVP, vamos tentar achar plugin que tenha nome similar ou mapeamento direto.
                    # Mas o prompt da IA define intents especificos: open_app, create_file, etc.
                    
                    plugin_map = {
                        "open_app": "OpenApp",
                        "create_file": "FileOps", # Cuidado: FileOps pode ter varias funcoes
                        "write_text": "FileOps",
                        "run_shell": "RunShell"
                    }
                    
                    target_plugin_name = plugin_map.get(intent)
                    if target_plugin_name and target_plugin_name in self.plugins:
                        matched_plugin = self.plugins[target_plugin_name]
                        command_name = intent
                        params = ai_result.get("parameters", {})
                        self.logger.info(f"AI roteou para plugin: {target_plugin_name}")

            except Exception as e:
                import traceback
                self.logger.error(f"Falha no AI Fallback: {e}")
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
                
                # Feedback de voz opcional para sucesso
                # self.speak(f"Comando {matched_plugin.name()} executado.") 
                
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
