# 🤖 Jarvis - Assistente de Voz Local

Um assistente de voz inteligente e local que respeita sua privacidade, construído com arquitetura modular e plugin-based.

## 🚀 Funcionalidades

- 🎤 **Reconhecimento de Voz Offline**: Suporte para Whisper e Vosk
- 🧠 **Processamento de Linguagem Natural**: Integração com Gemini AI
- 🔧 **Sistema de Plugins Extensível**: Arquitetura modular para fácil extensão
- 🛡️ **Controle de Segurança Avançado**: Múltiplos níveis de autonomia e validação
- 📱 **Interface Gráfica Intuitiva**: System tray e overlay visual
- 💾 **Sistema de Memória**: Memória de curto e longo prazo
- 🔍 **Verificação de Integridade**: Sistema completo de validação

## 📋 Pré-requisitos

- **Python 3.8+**
- **Windows/Linux/macOS**
- **Microfone** (para comandos de voz)
- **4GB+ RAM** (recomendado para modelos de IA)

## 🔧 Instalação Rápida

### 1. Clonar Repositório

```bash
git clone https://github.com/Bueno135/Jarvis.git
cd jarvis
```

### 2. Criar Ambiente Virtual

```bash
# Criar ambiente virtual
python -m venv jarvis-env

# Ativar ambiente
# Windows:
jarvis-env\Scripts\activate
# Linux/Mac:
source jarvis-env/bin/activate
```

### 3. Instalar Dependências

```bash
# Instalar dependências básicas
pip install pyyaml colorlog sounddevice numpy keyboard pystray Pillow

# Instalar dependências completas
pip install -r requirements.txt
```

### 4. Configurar API Keys (Opcional)

```bash
# Para funcionalidades de IA
export GEMINI_API_KEY="sua_chave_aqui"

# Windows
set GEMINI_API_KEY=sua_chave_aqui
```

### 5. Verificar Sistema

```bash
python verify_system.py
```

### 6. Executar Jarvis

```bash
# Modo texto
python main.py --text "echo hello world"

# Modo voz + interface
python main.py
```

## 🎮 Uso

### Comandos de Voz

Diga "Jarvis" seguido do comando:

- **"Jarvis, abra o notepad"** - Abre aplicativos
- **"Jarvis, que horas são?"** - Informações básicas
- **"Jarvis, crie um arquivo"** - Operações de arquivo
- **"Jarvis, calcule 2 + 2"** - Cálculos matemáticos

### Interface Gráfica

- **Ícone na bandeja do sistema**: Acesso rápido e status
- **Overlay visual**: Feedback visual em tempo real
- **Hotkey**: `Ctrl+Alt+J` para ativação manual

### Comandos de Texto

```bash
# Validar configuração
python main.py --validate-config

# Executar comando específico
python main.py --text "echo hello world"

# Verificar sistema
python main.py --check-system
```

## ⚙️ Configuração

### Arquivo de Configuração

Editar `config/config.yaml` para personalizar:

```yaml
app:
  name: "Jarvis"
  wake_word: "jarvis"  # Palavra de ativação
  language: "pt-BR"    # Idioma

logging:
  level: "INFO"       # DEBUG, INFO, WARNING, ERROR
  file: "logs/jarvis.json"

security:
  autonomy_mode: "semi_auto"  # manual, semi_auto, autonomous
  require_confirmation: true   # Confirmar comandos perigosos

ai:
  enabled: true       # Ativar processamento de IA
  provider: "gemini"  # Provedor de IA

stt:
  provider: "whisper" # whisper ou vosk
  model: "tiny"       # Modelo de reconhecimento
  language: "pt"      # Idioma do reconhecimento

tts:
  voice: "pt-BR-AntonioNeural"  # Voz para síntese
```

### Configuração de Áudio

```yaml
vad:
  energy_threshold: 300          # Sensibilidade do microfone
  silence_timeout_speech: 1.0    # Tempo de silêncio após fala
  silence_timeout_no_speech: 5.0 # Timeout sem fala
  max_buffer_seconds: 15         # Duração máxima de gravação
```

### Segurança

Criar `config/whitelist.yaml` para comandos permitidos:

```yaml
allowed_commands:
  - "echo *"
  - "date"
  - "time"
  - "notepad"
  - "calculator"
```

## 🧩 Desenvolvimento de Plugins

### Estrutura de Plugins

```
plugins/
├── system/
│   ├── echo.py          # Plugin de exemplo
│   ├── file_ops.py      # Operações de arquivo
│   └── automation.py    # Automação
├── web/
│   └── web_agent.py     # Agente web
└── base_plugin.py       # Classe base
```

### Criando um Plugin

```python
from plugins.base_plugin import BasePlugin
from core.interfaces import CommandContext, CommandResult

class MyPlugin(BasePlugin):
    def name(self) -> str:
        return "MyPlugin"
    
    def patterns(self) -> List[str]:
        return ["hello", "greet", "oi"]
    
    def validate_context(self, ctx: CommandContext) -> bool:
        return bool(ctx.raw_text.strip())
    
    def _execute_impl(self, ctx: CommandContext) -> CommandResult:
        message = f"Hello from {self.name()}!"
        return CommandResult(
            success=True,
            message=message,
            data={"plugin": self.name()}
        )
```

### Instalar Plugin

1. Criar arquivo em `plugins/category/my_plugin.py`
2. Implementar classe herdando de `BasePlugin`
3. Reiniciar Jarvis
4. Plugin será carregado automaticamente

## 🛡️ Segurança

### Níveis de Autonomia

- **Manual**: Todos os comandos requerem confirmação
- **Semi-Auto**: Comandos whitelist executados automaticamente
- **Autônomo**: Comandos não-perigosos executados automaticamente

### Validação de Comandos

- **Padrões perigosos**: `rm -rf`, `format c:`, etc.
- **Confirmação obrigatória**: Comandos de alto risco
- **Whitelist**: Comandos explicitamente permitidos

### Auditoria

- **Logging completo**: Todos os comandos logados
- **Rastreamento**: Histórico de execuções
- **Alertas**: Notificações de atividades suspeitas

## 🧪 Testes

### Executar Testes

```bash
# Todos os testes
python -m pytest tests/

# Testes de unidade
python -m pytest tests/ -m "unit"

# Testes de integração
python -m pytest tests/ -m "integration"

# Com coverage
python -m pytest --cov=core tests/
```

### Verificação de Integridade

```bash
# Verificação completa do sistema
python scripts/verify_system.py

# Ou usar o módulo diretamente
python -c "from core.integrity_checker import SystemIntegrityChecker; SystemIntegrityChecker().run_all_checks()"
```

## 🐛 Solução de Problemas

### Problemas Comuns

#### 1. **"ModuleNotFoundError"**
```bash
# Verificar instalação
pip list | grep -E "(yaml|sounddevice|numpy)"

# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

#### 2. **Microfone não funciona**
```bash
# Testar áudio
python -c "import sounddevice; print(sounddevice.query_devices())"

# Ajustar configuração
# Editar config.yaml -> vad -> energy_threshold
```

#### 3. **Reconhecimento falhando**
```bash
# Ajustar sensibilidade
# energy_threshold: 300 (mais sensível)
# energy_threshold: 1000 (menos sensível)

# Testar em ambiente silencioso
```

#### 4. **Plugin não carrega**
```bash
# Verificar estrutura
python -c "from core.plugin_loader import PluginLoader; print([p.name() for p in PluginLoader().discover_and_load()])"

# Verificar erros nos logs
tail -f logs/jarvis.json
```

#### 5. **IA não responde**
```bash
# Verificar API key
echo $GEMINI_API_KEY

# Testar conexão
python test_gemini.py
```

### Debug Mode

```bash
# Ativar logging debug
export JARVIS_LOG_LEVEL=DEBUG

# Ou editar config.yaml
logging:
  level: "DEBUG"
```

### Logs

- **Console**: Saída em tempo real
- **Arquivo**: `logs/jarvis.json` (estruturado)
- **Níveis**: DEBUG, INFO, WARNING, ERROR, CRITICAL

## 📊 Estrutura do Projeto

```
jarvis/
├── 📁 core/                    # Módulos principais do sistema
│   ├── kernel.py              # Orquestrador central
│   ├── security.py            # Gerenciamento de segurança
│   ├── plugin_loader.py       # Carregamento de plugins
│   ├── exceptions.py          # Exceções personalizadas
│   ├── metrics.py             # Sistema de métricas
│   ├── integrity_checker.py   # Verificação de integridade
│   ├── enhanced_audio.py      # Gerenciamento de áudio
│   ├── memory/                # Sistema de memória
│   ├── stt/                   # Speech-to-text
│   ├── tts/                   # Text-to-speech
│   ├── ai/                    # Inteligência artificial
│   ├── vision/                # Processamento de visão
│   └── web/                   # Serviços web
├── 📁 plugins/                 # Sistema de plugins
│   ├── base_plugin.py         # Classe base para plugins
│   ├── system/                # Plugins do sistema
│   └── web/                   # Plugins web
├── 📁 ui/                      # Interface do usuário
│   ├── ui_manager.py          # Gerenciador unificado
│   ├── tray.py                # System tray
│   └── overlay.py             # Interface visual
├── 📁 tests/                   # Testes automatizados
│   ├── conftest.py            # Configuração de testes
│   ├── test_integration_real.py
│   └── test_exceptions.py
├── 📁 scripts/                 # Scripts utilitários
│   ├── verify_system.py       # Verificação do sistema
│   ├── verify.py              # Verificação básica
│   └── test_gemini.py         # Teste da API Gemini
├── 📁 docs/                    # Documentação
│   ├── API.md                 # Documentação da API
│   ├── models.txt             # Informações sobre modelos
│   ├── PLANO_MELHORIA.md      # Plano de melhorias
│   └── prd.json               # Product requirements
├── 📁 config/                  # Arquivos de configuração
│   ├── config.yaml            # Configuração principal
│   └── whitelist.yaml         # Lista de comandos permitidos
├── 📁 tools/                   # Ferramentas de desenvolvimento
├── 📁 examples/                # Exemplos de uso
├── 📁 assets/                  # Recursos estáticos
├── 📁 data/                    # Dados do sistema
├── 📁 logs/                    # Logs do sistema
├── 📁 model/                   # Modelos de STT/TTS
├── 🐍 main.py                  # Ponto de entrada principal
├── 📋 requirements.txt         # Dependências Python
├── 📄 README.md               # Documentação principal
└── 🚫 .gitignore              # Arquivos ignorados pelo Git
```

### Fluxo de Execução

1. **Entrada**: Voz → STT → Texto
2. **Processamento**: Kernel → Plugin → Resultado
3. **Saída**: TTS → Áudio + UI

## 📈 Performance

### Recursos Recomendados

- **CPU**: 2+ cores (para processamento de áudio)
- **RAM**: 4GB+ (modelos de IA)
- **Armazenamento**: 2GB+ (modelos e cache)

### Otimizações

- **Lazy Loading**: Componentes carregados sob demanda
- **Caching**: Cache de modelos e resultados
- **Threading**: Processamento não-bloqueante
- **Memory Management**: Limpeza automática

## 🤝 Contribuição

### Como Contribuir

1. **Fork** o projeto
2. **Criar branch**: `git checkout -b feature/nova-funcionalidade`
3. **Implementar** com testes
4. **Commit**: `git commit -m "Add nova funcionalidade"`
5. **Push**: `git push origin feature/nova-funcionalidade`
6. **Pull Request**: Descrever mudanças

### Guia de Estilo

- **Python**: PEP 8
- **Documentação**: Docstrings em todos os métodos
- **Testes**: Cobertura >80%
- **Commits**: Mensagens claras e descritivas

### Issues

- **Bugs**: Usar template de bug report
- **Features**: Descrever caso de uso
- **Security**: Reportar privadamente

## 📝 Licença

Este projeto está licenciado sob a **MIT License** - ver arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **OpenAI Whisper** - Reconhecimento de voz
- **Google Gemini** - Processamento de linguagem
- **Python Community** - Ferramentas e bibliotecas
- **Contribuidores** - Todas as contribuições

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/usuario/jarvis/issues)
- **Discussions**: [GitHub Discussions](https://github.com/usuario/jarvis/discussions)
- **Wiki**: [Documentação adicional](https://github.com/usuario/jarvis/wiki)

## 🗺️ Roadmap

### v0.2.0 (Próximo)
- [ ] Melhorias na interface
- [ ] Mais plugins nativos
- [ ] Otimizações de performance

### v0.3.0 (Futuro)
- [ ] Suporte a múltiplos idiomas
- [ ] Integração com mais serviços
- [ ] Interface web

---

**⭐ Se este projeto ajudou você, considere dar uma estrela!**

**🔄 Mantido pela comunidade, para a comunidade.**
