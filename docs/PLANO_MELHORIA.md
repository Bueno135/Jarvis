# 📋 Plano de Melhoria - Projeto Jarvis

## 🎯 **Visão Geral**

Este documento detalha um plano completo para corrigir os erros críticos e melhorar a arquitetura do projeto Jarvis, um assistente de voz local. O plano está organizado por prioridade e inclui passos detalhados para cada item.

---

## 🚨 **Fase 1: Correções Críticas (Prioridade Imediata)**

### 1.1 Instalação de Dependências Faltantes

**Problema:** Módulos essenciais não instalados impedem a execução

**Passos:**
```bash
# 1. Criar ambiente virtual
python -m venv jarvis-env

# 2. Ativar ambiente virtual
# Windows:
jarvis-env\Scripts\activate
# Linux/Mac:
source jarvis-env/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Verificar instalação crítica
pip install pyyaml colorlog sounddevice numpy keyboard pystray Pillow

# 5. Testar importações básicas
python -c "import yaml, colorlog, sounddevice; print('✅ Dependências básicas OK')"
```

**Arquivos a modificar:**
- `requirements.txt` - Adicionar versões específicas
- `setup.py` - Criar para melhor gerenciamento

---

### 1.2 Implementação de Módulos Core Ausentes

#### 1.2.1 Módulo `core/security.py`

**Criar arquivo:** `core/security.py`

```python
"""
Security management for Jarvis.
Handles command validation, autonomy modes, and safety checks.
"""
from enum import Enum
from typing import List, Dict, Any, Optional
import logging
import re
import os
from .interfaces import CommandContext, CommandResult

class AutonomyMode(Enum):
    MANUAL = "manual"
    SEMI_AUTO = "semi_auto"
    FULL_AUTO = "full_auto"

class SecurityManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("Jarvis.Security")
        self.autonomy_mode = AutonomyMode(config.get("security", {}).get("autonomy_mode", "semi_auto"))
        self.command_whitelist = config.get("security", {}).get("command_whitelist", [])
        self.require_confirmation = config.get("security", {}).get("require_confirmation", True)
        
    def validate_command(self, ctx: CommandContext) -> CommandResult:
        """Validate if a command is safe to execute."""
        # Check whitelist
        if self.command_whitelist and ctx.command_name not in self.command_whitelist:
            return CommandResult(False, f"Command '{ctx.command_name}' not in whitelist")
            
        # Check for dangerous patterns
        dangerous_patterns = [
            r'rm\s+-rf',
            r'del\s+.*\/s',
            r'format\s+c:',
            r'sudo\s+rm',
            r'chmod\s+777',
            r'curl.*\|.*sh',
            r'wget.*\|.*bash'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, ctx.raw_text, re.IGNORECASE):
                self.logger.warning(f"Dangerous command detected: {ctx.raw_text}")
                return CommandResult(False, "Command contains dangerous patterns")
                
        return CommandResult(True, "Command validated")
        
    def requires_confirmation(self, ctx: CommandContext) -> bool:
        """Check if command requires user confirmation."""
        if not self.require_confirmation:
            return False
            
        high_risk_commands = ["delete", "remove", "format", "shutdown", "reboot"]
        return any(risk in ctx.raw_text.lower() for risk in high_risk_commands)
```

#### 1.2.2 Módulo `core/plugin_loader.py`

**Criar arquivo:** `core/plugin_loader.py`

```python
"""
Plugin loading system for Jarvis.
Discovers and loads plugins from the plugins directory.
"""
import os
import importlib
import inspect
import logging
from typing import List, Type, Dict, Any
from pathlib import Path

from .interfaces import PluginBase

class PluginLoader:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger("Jarvis.PluginLoader")
        self.plugins_path = Path(__file__).parent.parent / "plugins"
        self.loaded_plugins: Dict[str, PluginBase] = {}
        
    def discover_and_load(self) -> List[PluginBase]:
        """Discover and load all plugins."""
        loaded = []
        
        if not self.plugins_path.exists():
            self.logger.warning(f"Plugins directory not found: {self.plugins_path}")
            return loaded
            
        for plugin_dir in self.plugins_path.iterdir():
            if plugin_dir.is_dir() and not plugin_dir.name.startswith("__"):
                plugin = self._load_plugin_directory(plugin_dir)
                if plugin:
                    loaded.append(plugin)
                    
        self.logger.info(f"Loaded {len(loaded)} plugins")
        return loaded
        
    def _load_plugin_directory(self, plugin_dir: Path) -> PluginBase:
        """Load a single plugin from directory."""
        try:
            # Look for plugin files
            for py_file in plugin_dir.glob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                    
                module_name = f"plugins.{plugin_dir.name}.{py_file.stem}"
                module = importlib.import_module(module_name)
                
                # Find PluginBase classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, PluginBase) and obj != PluginBase:
                        plugin_instance = obj()
                        self.loaded_plugins[plugin_instance.name()] = plugin_instance
                        self.logger.info(f"Loaded plugin: {plugin_instance.name()}")
                        return plugin_instance
                        
        except Exception as e:
            self.logger.error(f"Failed to load plugin from {plugin_dir}: {e}")
            
        return None
```

#### 1.2.3 Módulo `core/task_planner.py`

**Criar arquivo:** `core/task_planner.py`

```python
"""
Task planning system for Jarvis.
Breaks down complex commands into executable steps.
"""
import logging
from typing import List, Dict, Any, Optional
from .interfaces import TaskPlan, TaskStep, TaskStatus, TaskPlannerBase, PluginBase
from .ai.gemini_client import GeminiClient

class TaskPlanner(TaskPlannerBase):
    def __init__(self, kernel):
        self.kernel = kernel
        self.logger = logging.getLogger("Jarvis.TaskPlanner")
        self.gemini_client = None
        
        try:
            self.gemini_client = GeminiClient(kernel.config)
        except Exception as e:
            self.logger.warning(f"Failed to initialize Gemini client: {e}")
            
    def plan(self, goal: str, available_plugins: List[str]) -> TaskPlan:
        """Generate a task plan to achieve the given goal."""
        try:
            if self.gemini_client:
                # Try AI-based planning
                ai_plan = self._ai_plan(goal, available_plugins)
                if ai_plan:
                    return ai_plan
                    
            # Fallback to rule-based planning
            return self._rule_based_plan(goal, available_plugins)
            
        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            return self._fallback_plan(goal)
            
    def _ai_plan(self, goal: str, available_plugins: List[str]) -> Optional[TaskPlan]:
        """Use AI to generate a plan."""
        try:
            prompt = f"""
            Break down this goal into steps: "{goal}"
            Available plugins: {', '.join(available_plugins)}
            
            Return a JSON plan with steps, each having:
            - description: what to do
            - plugin_name: which plugin to use
            - params: parameters for the plugin
            """
            
            response = self.gemini_client.generate_response(prompt)
            return self._parse_ai_response(response, goal)
            
        except Exception as e:
            self.logger.error(f"AI planning failed: {e}")
            return None
            
    def _rule_based_plan(self, goal: str, available_plugins: List[str]) -> TaskPlan:
        """Rule-based planning for common patterns."""
        steps = []
        
        # File operations
        if "create" in goal.lower() and "file" in goal.lower():
            if "FileOps" in available_plugins:
                steps.append(TaskStep(
                    id="1",
                    description="Create file",
                    plugin_name="FileOps",
                    params={"action": "create", "content": ""}
                ))
                
        # App operations
        if "open" in goal.lower() or "launch" in goal.lower():
            if "OpenApp" in available_plugins:
                app_name = self._extract_app_name(goal)
                steps.append(TaskStep(
                    id="1",
                    description=f"Open {app_name}",
                    plugin_name="OpenApp",
                    params={"app": app_name}
                ))
                
        return TaskPlan(goal=goal, steps=steps)
        
    def _extract_app_name(self, text: str) -> str:
        """Extract app name from command text."""
        # Simple extraction logic
        words = text.lower().split()
        apps = ["notepad", "calculator", "browser", "chrome", "firefox"]
        
        for word in words:
            if word in apps:
                return word
                
        return "unknown"
        
    def _parse_ai_response(self, response: str, goal: str) -> TaskPlan:
        """Parse AI response into TaskPlan."""
        # Implementation depends on AI response format
        # Placeholder for now
        return self._fallback_plan(goal)
        
    def _fallback_plan(self, goal: str) -> TaskPlan:
        """Create a simple fallback plan."""
        return TaskPlan(
            goal=goal,
            steps=[TaskStep(
                id="1",
                description=f"Execute: {goal}",
                plugin_name="Echo",
                params={}
            )]
        )
```

---

### 1.3 Correção de Importações Circulares

**Problema:** Módulos importam uns aos outros de forma circular

**Solução:** Implementar lazy imports

**Arquivos a modificar:**

#### `core/kernel.py` - Linhas 35-42
```python
# Substituir import direto por lazy import
# De:
from .security import SecurityManager
from .plugin_loader import PluginLoader

# Para:
def _get_security_manager(self):
    if not hasattr(self, '_security_manager'):
        from .security import SecurityManager
        self._security_manager = SecurityManager(self.config)
    return self._security_manager

def _get_plugin_loader(self):
    if not hasattr(self, '_plugin_loader'):
        from .plugin_loader import PluginLoader
        self._plugin_loader = PluginLoader(config=self.config)
    return self._plugin_loader
```

---

## ⚙️ **Fase 2: Melhorias Estruturais (Prioridade Alta)**

### 2.1 Padronização de Configuração

**Problema:** Configuração inconsistente entre wake word e nome

**Arquivo:** `config/config.yaml`

```yaml
app:
  name: "Jarvis"  # Padronizado
  version: "0.1.0"
  language: "pt-BR"  # Ajustado para português
  wake_word: "jarvis"  # Simplificado e padronizado

# Adicionar seção de validação
validation:
  check_dependencies: true
  verify_plugins: true
  log_level: "INFO"
```

### 2.2 Melhoria no Tratamento de Exceções

**Criar arquivo:** `core/exceptions.py`

```python
"""
Custom exceptions for Jarvis.
"""
class JarvisException(Exception):
    """Base exception for Jarvis."""
    pass

class ConfigurationError(JarvisException):
    """Configuration related errors."""
    pass

class PluginError(JarvisException):
    """Plugin related errors."""
    pass

class STTError(JarvisException):
    """Speech-to-text errors."""
    pass

class TTSError(JarvisException):
    """Text-to-speech errors."""
    pass

class SecurityError(JarvisException):
    """Security related errors."""
    pass
```

**Modificar logging em vários arquivos:**

#### `core/kernel.py` - Adicionar exceções específicas
```python
from .exceptions import PluginError, SecurityError

# Substituir exceções genéricas
try:
    result = matched_plugin.execute(ctx)
except PluginError as e:
    self.logger.error(f"Plugin error: {e}")
    return CommandResult(False, f"Plugin execution failed: {e}")
except SecurityError as e:
    self.logger.error(f"Security error: {e}")
    return CommandResult(False, f"Security violation: {e}")
except Exception as e:
    self.logger.error(f"Unexpected error: {e}")
    return CommandResult(False, f"Unexpected error: {e}")
```

---

## 🔧 **Fase 3: Melhorias Funcionais (Prioridade Média)**

### 3.1 Gerenciamento de Áudio Melhorado

**Problema:** Dependência de modelo Vosk não incluído

**Solução:** Implementar download automático e fallback

**Modificar:** `core/voice_loop.py`

```python
def _ensure_stt_model(self):
    """Ensure STT model is available."""
    if self.config.get("stt", {}).get("provider") == "vosk":
        model_path = "model"
        if not os.path.exists(model_path):
            self.logger.info("Downloading Vosk model...")
            self._download_vosk_model(model_path)
            
def _download_vosk_model(self, model_path: str):
    """Download Vosk model if not present."""
    try:
        import urllib.request
        import zipfile
        
        # URL para modelo pequeno em português
        model_url = "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"
        zip_path = "vosk-model.zip"
        
        self.logger.info(f"Downloading model from {model_url}")
        urllib.request.urlretrieve(model_url, zip_path)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(model_path)
            
        os.remove(zip_path)
        self.logger.info("Model downloaded successfully")
        
    except Exception as e:
        self.logger.error(f"Failed to download model: {e}")
        # Fallback para Whisper
        self.config["stt"]["provider"] = "whisper"
```

### 3.2 Arquitetura de Plugins Refatorada

**Criar arquivo:** `plugins/base_plugin.py`

```python
"""
Base plugin class with common functionality.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from core.interfaces import PluginBase, CommandContext, CommandResult
import logging

class BasePlugin(PluginBase):
    """Base class with common plugin functionality."""
    
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
```

### 3.3 Interface Unificada

**Criar arquivo:** `ui/ui_manager.py`

```python
"""
Unified UI manager for Jarvis.
Coordinates tray, overlay, and other UI components.
"""
import threading
import logging
from typing import Optional
from core.kernel import Kernel

class UIManager:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.logger = logging.getLogger("Jarvis.UIManager")
        self.tray = None
        self.overlay = None
        self.is_running = False
        
    def start(self):
        """Start all UI components."""
        try:
            # Start overlay in separate thread
            from ui.overlay import OverlayUI
            self.overlay = OverlayUI(self.kernel)
            overlay_thread = threading.Thread(target=self.overlay.run, daemon=True)
            overlay_thread.start()
            
            # Start tray in main thread
            from ui.tray import SystemTray
            self.tray = SystemTray(self.kernel)
            self.tray.run()
            
        except Exception as e:
            self.logger.error(f"Failed to start UI: {e}")
            
    def stop(self):
        """Stop all UI components."""
        if self.tray:
            self.tray.stop()
        if self.overlay:
            self.overlay.stop()
```

---

## 🧪 **Fase 4: Qualidade e Testes (Prioridade Média)**

### 4.1 Estrutura de Testes Melhorada

**Criar arquivo:** `tests/conftest.py`

```python
"""
Pytest configuration and fixtures.
"""
import pytest
import tempfile
import shutil
from unittest.mock import MagicMock
from core.kernel import Kernel
from core.config_validator import validate_config

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_config():
    """Mock configuration for tests."""
    config = {
        "app": {"name": "TestJarvis", "wake_word": "test"},
        "logging": {"level": "DEBUG"},
        "ai": {"enabled": False},
        "stt": {"provider": "whisper"},
        "security": {"autonomy_mode": "manual"}
    }
    return validate_config(config)[0]

@pytest.fixture
def mock_kernel(mock_config):
    """Mock kernel for tests."""
    kernel = MagicMock(spec=Kernel)
    kernel.config = mock_config
    return kernel
```

**Criar arquivo:** `tests/test_integration_real.py`

```python
"""
Integration tests with real components.
"""
import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_full_pipeline():
    """Test complete pipeline with real components."""
    try:
        from main import load_config
        from core.kernel import Kernel
        
        # Load real config
        config = load_config()
        
        # Initialize kernel
        kernel = Kernel(config)
        
        # Test basic command
        result = kernel.dispatch("test command")
        assert result is not None
        
    except ImportError as e:
        pytest.skip(f"Missing dependencies: {e}")
```

### 4.2 Verificação de Integridade

**Criar arquivo:** `verify_system.py`

```python
#!/usr/bin/env python3
"""
System verification script.
Checks all dependencies and components.
"""
import sys
import importlib
import os
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    required = [
        'yaml', 'colorlog', 'sounddevice', 'numpy', 
        'keyboard', 'pystray', 'Pillow', 'transformers'
    ]
    
    missing = []
    for dep in required:
        try:
            importlib.import_module(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}")
            missing.append(dep)
    
    return missing

def check_core_modules():
    """Check if all core modules exist."""
    core_path = Path("core")
    required_modules = [
        "kernel.py", "config_validator.py", "logger.py",
        "security.py", "plugin_loader.py", "task_planner.py"
    ]
    
    missing = []
    for module in required_modules:
        if not (core_path / module).exists():
            print(f"❌ {module}")
            missing.append(module)
        else:
            print(f"✅ {module}")
    
    return missing

def check_config():
    """Check configuration file."""
    config_path = Path("config/config.yaml")
    if config_path.exists():
        print("✅ config.yaml exists")
        return True
    else:
        print("❌ config.yaml missing")
        return False

def main():
    """Run all checks."""
    print("🔍 Verifying Jarvis System...")
    print()
    
    print("📦 Checking dependencies:")
    missing_deps = check_dependencies()
    print()
    
    print("🧩 Checking core modules:")
    missing_modules = check_core_modules()
    print()
    
    print("⚙️ Checking configuration:")
    config_ok = check_config()
    print()
    
    # Summary
    if missing_deps or missing_modules or not config_ok:
        print("❌ System verification failed!")
        if missing_deps:
            print(f"Missing dependencies: {missing_deps}")
        if missing_modules:
            print(f"Missing modules: {missing_modules}")
        return 1
    else:
        print("✅ System verification passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
```

---

## 📚 **Fase 5: Documentação (Prioridade Baixa)**

### 5.1 Documentação de API

**Criar arquivo:** `docs/API.md`

```markdown
# Jarvis API Documentation

## Core Components

### Kernel
The main orchestrator of the system.

#### Methods
- `dispatch(text: str) -> CommandResult`: Execute a command
- `speak(text: str)`: Convert text to speech
- `register_plugin(plugin: PluginBase)`: Register a new plugin

### PluginBase
Abstract base class for all plugins.

#### Required Methods
- `name() -> str`: Return plugin name
- `patterns() -> List[str]`: Return command patterns
- `execute(ctx: CommandContext) -> CommandResult`: Execute command

## Configuration

### Structure
```yaml
app:
  name: "Jarvis"
  wake_word: "jarvis"
  
logging:
  level: "INFO"
  file: "logs/jarvis.json"
  
ai:
  provider: "gemini"
  enabled: true
```

## Plugin Development

### Creating a Plugin
```python
from core.interfaces import PluginBase, CommandContext, CommandResult

class MyPlugin(PluginBase):
    def name(self) -> str:
        return "MyPlugin"
        
    def patterns(self) -> List[str]:
        return ["hello", "hi"]
        
    def execute(self, ctx: CommandContext) -> CommandResult:
        return CommandResult(True, "Hello from my plugin!")
```
```

### 5.2 README Melhorado

**Modificar:** `README.md`

```markdown
# 🤖 Jarvis - Assistente de Voz Local

Um assistente de voz inteligente e local que respeita sua privacidade.

## 🚀 Funcionalidades

- 🎤 Reconhecimento de voz offline (Whisper/Vosk)
- 🧠 Processamento de linguagem natural (Gemini)
- 🔧 Sistema de plugins extensível
- 🛡️ Controle de segurança e autonomia
- 📱 Interface gráfica intuitiva

## 📋 Pré-requisitos

- Python 3.8+
- Windows/Linux/macOS
- Microfone (para comandos de voz)

## 🔧 Instalação Rápida

```bash
# 1. Clonar repositório
git clone https://github.com/usuario/jarvis.git
cd jarvis

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar API keys (opcional)
export GEMINI_API_KEY="sua_chave_aqui"

# 5. Verificar sistema
python verify_system.py

# 6. Executar
python main.py
```

## 🎮 Uso

### Comandos de Voz
- "Jarvis, abra o notepad"
- "Jarvis, que horas são?"
- "Jarvis, crie um arquivo"

### Interface Gráfica
- Ícone na bandeja do sistema
- Overlay visual para feedback
- Controle via hotkey (Ctrl+Alt+J)

## 🔧 Configuração

Editar `config/config.yaml` para personalizar:

```yaml
app:
  wake_word: "jarvis"  # Palavra de ativação
  
stt:
  provider: "whisper"  # ou "vosk"
  
ai:
  enabled: true  # Desativar para modo offline
```

## 🧩 Plugins

Crie plugins personalizados em `plugins/`:

```python
from core.interfaces import PluginBase, CommandContext, CommandResult

class CustomPlugin(PluginBase):
    def name(self) -> str:
        return "Custom"
        
    def patterns(self) -> List[str]:
        return ["custom command"]
        
    def execute(self, ctx: CommandContext) -> CommandResult:
        # Sua lógica aqui
        return CommandResult(True, "Success!")
```

## 🛡️ Segurança

- Modos de autonomia: manual, semi-auto, auto
- Whitelist de comandos
- Validação de padrões perigosos
- Confirmação para operações de risco

## 🐛 Solução de Problemas

### Problemas Comuns

1. **"ModuleNotFoundError"**
   ```bash
   pip install -r requirements.txt
   ```

2. **Microfone não funciona**
   - Verifique permissões do sistema
   - Teste com `python -m sounddevice`

3. **Reconhecimento falhando**
   - Ajuste `energy_threshold` no config
   - Use ambiente silencioso

## 📝 Desenvolvimento

### Estrutura de Projeto
```
jarvis/
├── core/           # Lógica principal
├── plugins/        # Plugins do sistema
├── ui/            # Interface gráfica
├── config/        # Arquivos de configuração
├── tests/         # Testes automatizados
└── docs/          # Documentação
```

### Executar Testes
```bash
python -m pytest tests/
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie branch para sua feature
3. Faça commit das mudanças
4. Abra Pull Request

## 📄 Licença

MIT License - ver arquivo LICENSE

## 🙏 Agradecimentos

- OpenAI Whisper
- Google Gemini
- Comunidade Python
```

---

## 📊 **Cronograma de Implementação**

| Fase | Duração | Status | Responsável |
|------|---------|--------|-------------|
| Fase 1 - Crítico | 2-3 dias | ⏳ Planejado | Dev |
| Fase 2 - Estrutural | 3-4 dias | ⏳ Planejado | Dev |
| Fase 3 - Funcional | 4-5 dias | ⏳ Planejado | Dev |
| Fase 4 - Testes | 2-3 dias | ⏳ Planejado | QA |
| Fase 5 - Docs | 1-2 dias | ⏳ Planejado | Tech Writer |

---

## 🎯 **Métricas de Sucesso**

- [ ] Sistema executa sem erros de importação
- [ ] Todos os plugins carregam corretamente
- [ ] Interface responde a comandos
- [ ] Testes passam com >80%覆盖率
- [ ] Documentação completa e acessível

---

## 🔄 **Manutenção Contínua**

### Semanal
- Atualizar dependências
- Verificar logs de erros
- Testar integração

### Mensal
- Revisar segurança
- Otimizar performance
- Atualizar documentação

### Trimestral
- Refatorar arquitetura
- Adicionar novos recursos
- Planejar roadmap

---

**Última atualização:** 6 de Abril de 2026
**Versão do documento:** 1.0
