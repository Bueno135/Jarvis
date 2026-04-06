"""
Optional web interface for Jarvis.
Provides a modern web-based control panel.
"""
import json
import time
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import asdict
import logging
from datetime import datetime

try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    WEB_AVAILABLE = True
except ImportError:
    WEB_AVAILABLE = False

from core.kernel import Kernel
from core.metrics import get_success_metrics
from core.integrity_checker import SystemIntegrityChecker
from core.continuous_learning import get_continuous_learning

class WebInterface:
    """Web interface for Jarvis control and monitoring."""
    
    def __init__(self, kernel: Kernel, config: Dict[str, Any] = None):
        if not WEB_AVAILABLE:
            raise ImportError("FastAPI and related packages are required for web interface")
        
        self.kernel = kernel
        self.config = config or {}
        self.logger = logging.getLogger("Jarvis.WebInterface")
        
        # Configuration
        self.host = self.config.get("host", "localhost")
        self.port = self.config.get("port", 8080)
        self.debug = self.config.get("debug", False)
        self.enable_cors = self.config.get("enable_cors", True)
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Jarvis Web Interface",
            description="Web control panel for Jarvis AI Assistant",
            version="1.0.0"
        )
        
        # Setup CORS
        if self.enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        
        # WebSocket connections
        self.websocket_connections: List[WebSocket] = []
        
        # Setup routes
        self._setup_routes()
        
        # Static files
        self._setup_static_files()
        
        self.logger.info(f"Web interface configured on {self.host}:{self.port}")
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """Serve the main web interface."""
            return self._get_main_html()
        
        @self.app.get("/api/status")
        async def get_status():
            """Get system status."""
            return {
                "status": "running",
                "kernel_state": self.kernel.state.value,
                "plugins_loaded": len(self.kernel.plugins),
                "uptime": time.time() - getattr(self.kernel, 'start_time', time.time()),
                "timestamp": time.time()
            }
        
        @self.app.get("/api/plugins")
        async def get_plugins():
            """Get list of loaded plugins."""
            plugins = []
            for name, plugin in self.kernel.plugins.items():
                plugins.append({
                    "name": name,
                    "patterns": plugin.patterns(),
                    "class": plugin.__class__.__name__
                })
            return plugins
        
        @self.app.post("/api/command")
        async def execute_command(command: Dict[str, Any]):
            """Execute a command."""
            try:
                text = command.get("text", "")
                if not text:
                    raise HTTPException(status_code=400, detail="Command text is required")
                
                result = self.kernel.dispatch(text)
                
                return {
                    "success": result.success,
                    "message": result.message,
                    "data": result.data,
                    "timestamp": time.time()
                }
                
            except Exception as e:
                self.logger.error(f"Command execution failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/metrics")
        async def get_metrics():
            """Get system metrics."""
            try:
                metrics = get_success_metrics()
                return metrics.get_success_report()
            except Exception as e:
                self.logger.error(f"Failed to get metrics: {e}")
                return {"error": str(e)}
        
        @self.app.get("/api/health")
        async def health_check():
            """Perform health check."""
            try:
                checker = SystemIntegrityChecker()
                results = checker.run_all_checks()
                
                overall_status = checker.get_overall_status()
                
                return {
                    "status": overall_status.value,
                    "checks": len(results),
                    "passed": sum(1 for r in results if r.status.value == "✅"),
                    "timestamp": time.time()
                }
                
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                return {
                    "status": "❌",
                    "error": str(e),
                    "timestamp": time.time()
                }
        
        @self.app.get("/api/learning/preferences")
        async def get_learning_preferences():
            """Get learned user preferences."""
            try:
                learning = get_continuous_learning()
                preferences = learning.get_user_preferences()
                return preferences
            except Exception as e:
                self.logger.error(f"Failed to get preferences: {e}")
                return {"error": str(e)}
        
        @self.app.post("/api/learning/feedback")
        async def record_feedback(feedback: Dict[str, Any]):
            """Record user feedback."""
            try:
                learning = get_continuous_learning()
                # This would need the actual interaction ID
                # For now, just acknowledge
                return {"status": "recorded"}
            except Exception as e:
                self.logger.error(f"Failed to record feedback: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/config")
        async def get_config():
            """Get current configuration."""
            # Return sanitized config (no sensitive data)
            safe_config = {
                "app": self.kernel.config.get("app", {}),
                "logging": self.kernel.config.get("logging", {}),
                "plugins": self.kernel.config.get("plugins", {}),
                "ai": {
                    "enabled": self.kernel.config.get("ai", {}).get("enabled", False),
                    "provider": self.kernel.config.get("ai", {}).get("provider", "unknown")
                }
            }
            return safe_config
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                while True:
                    # Receive message
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle different message types
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))
                    elif message.get("type") == "command":
                        # Execute command and send result
                        result = self.kernel.dispatch(message.get("text", ""))
                        await websocket.send_text(json.dumps({
                            "type": "command_result",
                            "result": {
                                "success": result.success,
                                "message": result.message,
                                "data": result.data
                            }
                        }))
                    
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
        
        @self.app.get("/api/logs")
        async def get_logs(limit: int = 100):
            """Get recent logs."""
            try:
                logs_file = Path("logs/jarvis.json")
                if not logs_file.exists():
                    return []
                
                logs = []
                with open(logs_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-limit:]:
                        try:
                            log_entry = json.loads(line.strip())
                            logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
                
                return logs
                
            except Exception as e:
                self.logger.error(f"Failed to get logs: {e}")
                return {"error": str(e)}
    
    def _setup_static_files(self):
        """Setup static file serving."""
        # Create static directory if it doesn't exist
        static_dir = Path("web/static")
        static_dir.mkdir(parents=True, exist_ok=True)
        
        # Mount static files
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    def _get_main_html(self) -> str:
        """Generate the main HTML page."""
        return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jarvis Web Interface</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        .header h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 1.1em;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .status-item {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        
        .status-item strong {
            display: block;
            color: #333;
            margin-bottom: 5px;
        }
        
        .status-item span {
            color: #666;
            font-size: 0.9em;
        }
        
        .command-input {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .command-input input {
            flex: 1;
            padding: 12px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 1em;
        }
        
        .command-input button {
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s;
        }
        
        .command-input button:hover {
            background: #5a6fd8;
        }
        
        .command-result {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            margin-top: 10px;
            min-height: 60px;
        }
        
        .success {
            border-left: 4px solid #28a745;
        }
        
        .error {
            border-left: 4px solid #dc3545;
        }
        
        .plugins-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .plugin-item {
            padding: 10px;
            background: #f8f9fa;
            border-radius: 6px;
            margin-bottom: 8px;
        }
        
        .plugin-name {
            font-weight: bold;
            color: #333;
        }
        
        .plugin-patterns {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .metric-item {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .metric-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .logs-container {
            max-height: 400px;
            overflow-y: auto;
            background: #1e1e1e;
            border-radius: 8px;
            padding: 15px;
        }
        
        .log-entry {
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            margin-bottom: 5px;
            color: #ddd;
        }
        
        .log-time {
            color: #888;
        }
        
        .log-level-info {
            color: #17a2b8;
        }
        
        .log-level-error {
            color: #dc3545;
        }
        
        .log-level-warning {
            color: #ffc107;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .status-grid,
            .metrics-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Jarvis Web Interface</h1>
            <p>Control e monitore seu assistente de voz</p>
        </div>
        
        <div class="main-content">
            <div class="card">
                <h2>📊 Status do Sistema</h2>
                <div class="status-grid" id="status-grid">
                    <div class="status-item">
                        <strong>Estado</strong>
                        <span id="kernel-state">Carregando...</span>
                    </div>
                    <div class="status-item">
                        <strong>Plugins</strong>
                        <span id="plugins-count">Carregando...</span>
                    </div>
                    <div class="status-item">
                        <strong>Uptime</strong>
                        <span id="uptime">Carregando...</span>
                    </div>
                    <div class="status-item">
                        <strong>Saúde</strong>
                        <span id="health-status">Carregando...</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>🎤 Executar Comando</h2>
                <div class="command-input">
                    <input type="text" id="command-input" placeholder="Digite um comando..." />
                    <button onclick="executeCommand()">Executar</button>
                </div>
                <div id="command-result" class="command-result">
                    Resultado do comando aparecerá aqui...
                </div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="card">
                <h2>🔌 Plugins Carregados</h2>
                <div class="plugins-list" id="plugins-list">
                    Carregando plugins...
                </div>
            </div>
            
            <div class="card">
                <h2>📈 Métricas</h2>
                <div class="metrics-grid" id="metrics-grid">
                    <div class="metric-item">
                        <div class="metric-value" id="success-rate">-</div>
                        <div class="metric-label">Taxa de Sucesso</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value" id="commands-per-hour">-</div>
                        <div class="metric-label">Comandos/Hora</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value" id="avg-response-time">-</div>
                        <div class="metric-label">Tempo Médio</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value" id="error-rate">-</div>
                        <div class="metric-label">Taxa de Erro</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>📋 Logs Recentes</h2>
            <div class="logs-container" id="logs-container">
                Carregando logs...
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        
        // Initialize WebSocket connection
        function initWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                console.log('WebSocket connected');
                // Send ping every 30 seconds
                setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({type: 'ping'}));
                    }
                }, 30000);
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'pong') {
                    console.log('WebSocket pong received');
                }
            };
            
            ws.onclose = function() {
                console.log('WebSocket disconnected');
                // Try to reconnect after 5 seconds
                setTimeout(initWebSocket, 5000);
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        // Fetch system status
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                document.getElementById('kernel-state').textContent = data.kernel_state;
                document.getElementById('plugins-count').textContent = data.plugins_loaded;
                document.getElementById('uptime').textContent = formatUptime(data.uptime);
                
                // Update health status
                const healthResponse = await fetch('/api/health');
                const healthData = await healthResponse.json();
                document.getElementById('health-status').textContent = healthData.status;
                
            } catch (error) {
                console.error('Failed to update status:', error);
            }
        }
        
        // Fetch plugins
        async function updatePlugins() {
            try {
                const response = await fetch('/api/plugins');
                const plugins = await response.json();
                
                const pluginsList = document.getElementById('plugins-list');
                pluginsList.innerHTML = '';
                
                plugins.forEach(plugin => {
                    const pluginDiv = document.createElement('div');
                    pluginDiv.className = 'plugin-item';
                    pluginDiv.innerHTML = `
                        <div class="plugin-name">${plugin.name}</div>
                        <div class="plugin-patterns">Padrões: ${plugin.patterns.join(', ')}</div>
                    `;
                    pluginsList.appendChild(pluginDiv);
                });
                
            } catch (error) {
                console.error('Failed to update plugins:', error);
            }
        }
        
        // Fetch metrics
        async function updateMetrics() {
            try {
                const response = await fetch('/api/metrics');
                const data = await response.json();
                
                if (data.key_indicators) {
                    document.getElementById('success-rate').textContent = 
                        Math.round(data.key_indicators.success_rate) + '%';
                    document.getElementById('commands-per-hour').textContent = 
                        data.key_indicators.commands_per_hour.toFixed(1);
                    document.getElementById('avg-response-time').textContent = 
                        data.key_indicators.average_response_time.toFixed(2) + 's';
                    document.getElementById('error-rate').textContent = 
                        Math.round(data.key_indicators.error_rate) + '%';
                }
                
            } catch (error) {
                console.error('Failed to update metrics:', error);
            }
        }
        
        // Fetch logs
        async function updateLogs() {
            try {
                const response = await fetch('/api/logs?limit=50');
                const logs = await response.json();
                
                const logsContainer = document.getElementById('logs-container');
                logsContainer.innerHTML = '';
                
                logs.forEach(log => {
                    const logDiv = document.createElement('div');
                    logDiv.className = 'log-entry';
                    
                    const time = new Date(log.timestamp * 1000).toLocaleTimeString();
                    const levelClass = `log-level-${log.level.toLowerCase()}`;
                    
                    logDiv.innerHTML = `
                        <span class="log-time">[${time}]</span>
                        <span class="${levelClass}">${log.level}</span>
                        <span>${log.message}</span>
                    `;
                    
                    logsContainer.appendChild(logDiv);
                });
                
                // Scroll to bottom
                logsContainer.scrollTop = logsContainer.scrollHeight;
                
            } catch (error) {
                console.error('Failed to update logs:', error);
            }
        }
        
        // Execute command
        async function executeCommand() {
            const input = document.getElementById('command-input');
            const resultDiv = document.getElementById('command-result');
            const command = input.value.trim();
            
            if (!command) return;
            
            // Clear previous result
            resultDiv.innerHTML = 'Executando comando...';
            resultDiv.className = 'command-result';
            
            try {
                const response = await fetch('/api/command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ text: command })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultDiv.innerHTML = `✅ ${data.message}`;
                    resultDiv.classList.add('success');
                } else {
                    resultDiv.innerHTML = `❌ ${data.message}`;
                    resultDiv.classList.add('error');
                }
                
                // Clear input
                input.value = '';
                
                // Update status after command
                setTimeout(updateStatus, 1000);
                
            } catch (error) {
                resultDiv.innerHTML = `❌ Erro: ${error.message}`;
                resultDiv.classList.add('error');
            }
        }
        
        // Format uptime
        function formatUptime(seconds) {
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${minutes}m`;
        }
        
        // Handle Enter key in command input
        document.getElementById('command-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                executeCommand();
            }
        });
        
        // Initialize everything
        function init() {
            initWebSocket();
            updateStatus();
            updatePlugins();
            updateMetrics();
            updateLogs();
            
            // Update every 5 seconds
            setInterval(() => {
                updateStatus();
                updateMetrics();
            }, 5000);
            
            // Update logs every 10 seconds
            setInterval(updateLogs, 10000);
        }
        
        // Start when page loads
        window.addEventListener('load', init);
    </script>
</body>
</html>
        """
    
    async def start_server(self):
        """Start the web server."""
        if not WEB_AVAILABLE:
            self.logger.error("Web interface dependencies not available")
            return False
        
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info" if self.debug else "warning"
        )
        
        server = uvicorn.Server(config)
        
        self.logger.info(f"Starting web interface on http://{self.host}:{self.port}")
        
        try:
            await server.serve()
        except Exception as e:
            self.logger.error(f"Failed to start web server: {e}")
            return False
        
        return True
    
    def stop_server(self):
        """Stop the web server."""
        # Close WebSocket connections
        for ws in self.websocket_connections:
            ws.close()
        
        self.websocket_connections.clear()
        self.logger.info("Web interface stopped")

# Factory function
def create_web_interface(kernel: Kernel, config: Dict[str, Any] = None) -> Optional[WebInterface]:
    """Create web interface if dependencies are available."""
    if not WEB_AVAILABLE:
        logging.warning("Web interface dependencies not available. Install with: pip install fastapi uvicorn")
        return None
    
    return WebInterface(kernel, config)

# CLI command to start web interface
async def start_web_interface_cli(kernel: Kernel, config: Dict[str, Any] = None):
    """Start web interface from CLI."""
    web_interface = create_web_interface(kernel, config)
    
    if web_interface:
        await web_interface.start_server()
    else:
        print("Web interface not available. Install required dependencies.")
        print("Run: pip install fastapi uvicorn")
