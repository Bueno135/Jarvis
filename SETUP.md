# 🚀 Jarvis Setup Rápido

Este guia ajuda você a configurar o Jarvis rapidamente em seu sistema.

## ⚡ Setup Automático (Recomendado)

### 1. Clonar o Repositório
```bash
git clone https://github.com/Bueno135/Jarvis.git
cd Jarvis
```

### 2. Criar Ambiente Virtual
```bash
python -m venv jarvis-env

# Windows
jarvis-env\Scripts\activate

# Linux/Mac
source jarvis-env/bin/activate
```

### 3. Verificar Dependências
```bash
python scripts/check_dependencies.py
```

Este script irá:
- ✅ Verificar a versão do Python
- ✅ Instalar todas as dependências necessárias
- ✅ Testar se o Jarvis funciona
- ✅ Configurar o sistema automaticamente

### 4. Testar o Jarvis
```bash
# Teste em modo texto
python main.py --text "echo hello world"

# Iniciar com voz e interface
python main.py
```

## 🔧 Manual Setup (Se o automático falhar)

### Instalar Dependências Manualmente
```bash
pip install -r requirements-full.txt
```

### Verificar Componentes
```bash
# Verificar sistema
python verify_system.py

# Testar voz
python -c "import sounddevice; print(sounddevice.query_devices())"

# Testar TTS
python -c "import edge_tts; print('TTS OK')"
```

## 🌟 Primeiros Comandos

### Comandos Básicos
```bash
# Diga "Jarvis, echo hello world"
# Ou use modo texto:
python main.py --text "echo hello world"

# Outros comandos:
python main.py --text "que horas são?"
python main.py --text "abra o notepad"
python main.py --text "crie um arquivo teste.txt"
```

### Comandos de Voz
- "Jarvis, abra o notepad"
- "Jarvis, que horas são?"
- "Jarvis, calcule 2 + 2"
- "Jarvis, desligue o computador"

## ⚙️ Configuração Opcional

### API Key para IA (Opcional)
Para funcionalidades avançadas de IA:
```bash
# Windows
set GEMINI_API_KEY=sua_chave_aqui

# Linux/Mac
export GEMINI_API_KEY="sua_chave_aqui"
```

### Configurar Áudio
Se o reconhecimento de voz não funcionar:
1. Verifique o microfone
2. Ajuste a sensibilidade em `config/config.yaml`:
```yaml
vad:
  energy_threshold: 300  # Aumente se não reconhecer, diminua se pegar ruído
```

## 🐛 Solução de Problemas

### Problemas Comuns

#### 1. "No module named 'torch'"
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

#### 2. "No module named 'pygame'"
- ✅ Já foi corrigido! O Jarvis agora usa o player de áudio do sistema.

#### 3. "No module named 'transformers'"
```bash
pip install transformers
```

#### 4. Áudio não funciona
```bash
# Verificar dispositivos de áudio
python -c "import sounddevice; print(sounddevice.query_devices())"

# Testar gravação
python -c "import sounddevice; sd.rec(int(44100*2), 44100, 1); sd.wait()"
```

#### 5. Plugins não carregam
```bash
# Verificar plugins
python -c "from core.plugin_loader import PluginLoader; print([p.name() for p in PluginLoader().discover_and_load()])"
```

### Logs e Debug
```bash
# Ativar modo debug
python main.py --debug

# Verificar logs
tail -f logs/jarvis.json
```

## 📊 Verificar Funcionamento

### Teste Completo
```bash
python scripts/check_dependencies.py
```

### Teste Individual
```bash
# Testar kernel
python -c "from main import load_config; from core.kernel import Kernel; kernel=Kernel(load_config()); print('Kernel OK')"

# Testar plugins
python -c "from core.plugin_loader import PluginLoader; print(f'Plugins: {len(PluginLoader().discover_and_load())}')"

# Testar voz
python -c "import sounddevice; print('Áudio OK')"

# Testar TTS
python -c "import edge_tts; print('TTS OK')"
```

## 🎯 Próximos Passos

1. **Explore os plugins disponíveis**:
   - Echo: Repetir comandos
   - FileOps: Operações de arquivo
   - Automation: Automação de GUI
   - Vision: Análise de tela
   - WebAgent: Navegação web

2. **Configure suas preferências** em `config/config.yaml`

3. **Crie seus próprios plugins** seguindo o guia em `docs/DEVELOPMENT_GUIDE.md`

4. **Experimente as funcionalidades avançadas**:
   - Cache inteligente
   - Agendamento de tarefas
   - Aprendizado contínuo
   - Interface web

## 📞 Ajuda

- **Documentação completa**: `docs/`
- **Exemplos**: `examples/`
- **Issues**: [GitHub Issues](https://github.com/Bueno135/Jarvis/issues)
- **Discussões**: [GitHub Discussions](https://github.com/Bueno135/Jarvis/discussions)

## ✅ Checklist de Setup

- [ ] Python 3.8+ instalado
- [ ] Ambiente virtual criado
- [ ] Dependências instaladas
- [ ] Jarvis inicia sem erros
- [ ] Comando "echo hello world" funciona
- [ ] Microfone funciona (para comandos de voz)
- [ ] TTS funciona (sintetização de voz)

---

**🎉 Parabéns! Seu Jarvis está pronto para usar!**

Comece dizendo "Jarvis, echo hello world" ou use `python main.py --text "echo hello world"`
