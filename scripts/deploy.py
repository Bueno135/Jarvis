#!/usr/bin/env python3
"""
Jarvis Deployment Script
Automates deployment for different environments.
"""
import os
import sys
import json
import shutil
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class JarvisDeployer:
    """Handles Jarvis deployment for different environments."""
    
    def __init__(self, config_file: str = "deploy_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.project_root = Path(__file__).parent.parent
        self.deploy_dir = self.project_root / "deploy"
        
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration."""
        default_config = {
            "environments": {
                "development": {
                    "python_version": "3.8",
                    "requirements": "requirements.txt",
                    "environment_file": ".env.development",
                    "services": ["kernel", "web"],
                    "debug": True,
                    "log_level": "DEBUG"
                },
                "staging": {
                    "python_version": "3.9",
                    "requirements": "requirements.txt",
                    "environment_file": ".env.staging",
                    "services": ["kernel", "web", "scheduler"],
                    "debug": False,
                    "log_level": "INFO"
                },
                "production": {
                    "python_version": "3.10",
                    "requirements": "requirements.txt",
                    "environment_file": ".env.production",
                    "services": ["kernel", "web", "scheduler", "monitoring"],
                    "debug": False,
                    "log_level": "WARNING"
                }
            },
            "docker": {
                "base_image": "python:3.10-slim",
                "expose_ports": [8080],
                "volumes": ["./data:/app/data", "./logs:/app/logs"],
                "environment_vars": ["PYTHONPATH=/app"]
            },
            "systemd": {
                "user": "jarvis",
                "group": "jarvis",
                "working_directory": "/opt/jarvis",
                "restart_policy": "always"
            }
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                user_config = json.load(f)
                # Merge with default config
                default_config.update(user_config)
        
        return default_config
    
    def deploy(self, environment: str, method: str = "local") -> bool:
        """Deploy Jarvis to specified environment."""
        print(f"🚀 Deploying Jarvis to {environment} using {method} method")
        
        if environment not in self.config["environments"]:
            print(f"❌ Unknown environment: {environment}")
            return False
        
        env_config = self.config["environments"][environment]
        
        # Pre-deployment checks
        if not self._pre_deployment_checks(environment, env_config):
            return False
        
        # Create deployment directory
        self._create_deployment_directory(environment)
        
        # Deploy based on method
        if method == "local":
            success = self._deploy_local(environment, env_config)
        elif method == "docker":
            success = self._deploy_docker(environment, env_config)
        elif method == "systemd":
            success = self._deploy_systemd(environment, env_config)
        else:
            print(f"❌ Unknown deployment method: {method}")
            return False
        
        if success:
            self._post_deployment_setup(environment, env_config)
            print(f"✅ Successfully deployed to {environment}")
        else:
            print(f"❌ Failed to deploy to {environment}")
        
        return success
    
    def _pre_deployment_checks(self, environment: str, env_config: Dict[str, Any]) -> bool:
        """Run pre-deployment checks."""
        print("🔍 Running pre-deployment checks...")
        
        # Check Python version
        required_version = env_config["python_version"]
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        
        if not self._check_python_version(required_version):
            print(f"❌ Python {required_version} required, found {current_version}")
            return False
        
        # Check requirements file
        req_file = self.project_root / env_config["requirements"]
        if not req_file.exists():
            print(f"❌ Requirements file not found: {req_file}")
            return False
        
        # Check environment file
        env_file = self.project_root / env_config["environment_file"]
        if env_file.exists():
            print(f"📄 Using environment file: {env_file}")
        else:
            print(f"⚠️ Environment file not found: {env_file}")
        
        # Run tests
        if not self._run_tests():
            print("❌ Tests failed")
            return False
        
        print("✅ Pre-deployment checks passed")
        return True
    
    def _check_python_version(self, required_version: str) -> bool:
        """Check if Python version meets requirements."""
        major, minor = map(int, required_version.split('.'))
        return sys.version_info >= (major, minor)
    
    def _run_tests(self) -> bool:
        """Run test suite."""
        print("🧪 Running test suite...")
        
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✅ All tests passed")
                return True
            else:
                print(f"❌ Tests failed:\n{result.stdout}\n{result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Tests timed out")
            return False
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False
    
    def _create_deployment_directory(self, environment: str):
        """Create deployment directory structure."""
        deploy_env_dir = self.deploy_dir / environment
        deploy_env_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        subdirs = ["data", "logs", "config", "models", "cache"]
        for subdir in subdirs:
            (deploy_env_dir / subdir).mkdir(exist_ok=True)
    
    def _deploy_local(self, environment: str, env_config: Dict[str, Any]) -> bool:
        """Deploy locally."""
        print("📦 Deploying locally...")
        
        deploy_env_dir = self.deploy_dir / environment
        
        # Copy source files
        source_dirs = ["core", "plugins", "ui", "main.py"]
        for source in source_dirs:
            source_path = self.project_root / source
            if source_path.exists():
                if source_path.is_dir():
                    dest_path = deploy_env_dir / source
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(source_path, dest_path)
                else:
                    shutil.copy2(source_path, deploy_env_dir)
        
        # Copy config files
        config_dirs = ["config"]
        for config_dir in config_dirs:
            config_path = self.project_root / config_dir
            if config_path.exists():
                dest_config = deploy_env_dir / config_dir
                if dest_config.exists():
                    shutil.rmtree(dest_config)
                shutil.copytree(config_path, dest_config)
        
        # Install requirements
        if not self._install_requirements(deploy_env_dir, env_config):
            return False
        
        # Create startup scripts
        self._create_startup_scripts(deploy_env_dir, env_config)
        
        return True
    
    def _deploy_docker(self, environment: str, env_config: Dict[str, Any]) -> bool:
        """Deploy using Docker."""
        print("🐳 Deploying with Docker...")
        
        # Create Dockerfile
        dockerfile_content = self._generate_dockerfile(env_config)
        dockerfile_path = self.deploy_dir / environment / "Dockerfile"
        
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        # Create docker-compose.yml
        compose_content = self._generate_docker_compose(env_config)
        compose_path = self.deploy_dir / environment / "docker-compose.yml"
        
        with open(compose_path, 'w') as f:
            f.write(compose_content)
        
        # Build and run containers
        deploy_env_dir = self.deploy_dir / environment
        
        try:
            # Build image
            subprocess.run(
                ["docker", "build", "-t", f"jarvis-{environment}", "."],
                cwd=deploy_env_dir,
                check=True
            )
            
            # Run with docker-compose
            subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=deploy_env_dir,
                check=True
            )
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker deployment failed: {e}")
            return False
    
    def _deploy_systemd(self, environment: str, env_config: Dict[str, Any]) -> bool:
        """Deploy using systemd services."""
        print("⚙️ Deploying with systemd...")
        
        deploy_env_dir = self.deploy_dir / environment
        
        # First deploy locally
        if not self._deploy_local(environment, env_config):
            return False
        
        # Create systemd service files
        services = env_config["services"]
        for service in services:
            service_content = self._generate_systemd_service(service, env_config)
            service_file = f"/etc/systemd/system/jarvis-{service}.service"
            
            try:
                with open(service_file, 'w') as f:
                    f.write(service_content)
                
                # Enable and start service
                subprocess.run(["systemctl", "enable", f"jarvis-{service}"], check=True)
                subprocess.run(["systemctl", "start", f"jarvis-{service}"], check=True)
                
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to create service {service}: {e}")
                return False
        
        return True
    
    def _install_requirements(self, deploy_dir: Path, env_config: Dict[str, Any]) -> bool:
        """Install Python requirements."""
        print("📦 Installing requirements...")
        
        req_file = self.project_root / env_config["requirements"]
        
        try:
            subprocess.run(
                ["python", "-m", "pip", "install", "-r", str(req_file)],
                cwd=deploy_dir,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install requirements: {e}")
            return False
    
    def _create_startup_scripts(self, deploy_dir: Path, env_config: Dict[str, Any]):
        """Create startup scripts."""
        services = env_config["services"]
        
        # Create main startup script
        startup_script = deploy_dir / "start.sh"
        with open(startup_script, 'w') as f:
            f.write(f"""#!/bin/bash
# Jarvis Startup Script for {deploy_dir.name}

export PYTHONPATH={deploy_dir}
export JARVIS_ENV={deploy_dir.name}
export LOG_LEVEL={env_config.get('log_level', 'INFO')}

# Load environment file
if [ -f "{env_config['environment_file']}" ]; then
    export $(cat {env_config['environment_file']} | xargs)
fi

echo "🚀 Starting Jarvis in {deploy_dir.name} environment..."

# Start services
""")
            
            for service in services:
                if service == "kernel":
                    f.write("echo 'Starting kernel...'\n")
                    f.write("python main.py --daemon\n")
                elif service == "web":
                    f.write("echo 'Starting web interface...'\n")
                    f.write("python -c 'from main import load_config; from core.kernel import Kernel; from core.web_interface import create_web_interface; import asyncio; kernel=Kernel(load_config()); web=create_web_interface(kernel); asyncio.run(web.start_server())' &\n")
                elif service == "scheduler":
                    f.write("echo 'Starting task scheduler...'\n")
                    f.write("python -c 'from core.task_scheduler import get_task_scheduler; scheduler=get_task_scheduler(); input()' &\n")
            
            f.write("\necho '✅ Jarvis started successfully'\n")
        
        startup_script.chmod(0o755)
        
        # Create stop script
        stop_script = deploy_dir / "stop.sh"
        with open(stop_script, 'w') as f:
            f.write("""#!/bin/bash
# Jarvis Stop Script

echo "🛑 Stopping Jarvis..."

# Kill all Jarvis processes
pkill -f "python.*main.py"
pkill -f "python.*web_interface"
pkill -f "python.*task_scheduler"

echo "✅ Jarvis stopped"
""")
        
        stop_script.chmod(0o755)
    
    def _generate_dockerfile(self, env_config: Dict[str, Any]) -> str:
        """Generate Dockerfile content."""
        base_image = self.config["docker"]["base_image"]
        
        return f"""FROM {base_image}

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    portaudio19-dev \\
    python3-dev \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ ./core/
COPY plugins/ ./plugins/
COPY ui/ ./ui/
COPY config/ ./config/
COPY main.py .

# Create directories
RUN mkdir -p data logs models cache

# Set environment variables
ENV PYTHONPATH=/app
ENV JARVIS_ENV={env_config.get('environment_file', '.env')}

# Expose ports
{self._generate_expose_ports()}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "from main import load_config; from core.kernel import Kernel; Kernel(load_config())" || exit 1

# Start command
CMD ["python", "main.py"]
"""
    
    def _generate_docker_compose(self, env_config: Dict[str, Any]) -> str:
        """Generate docker-compose.yml content."""
        volumes = self.config["docker"]["volumes"]
        environment_vars = self.config["docker"]["environment_vars"]
        
        return f"""version: '3.8'

services:
  jarvis:
    build: .
    container_name: jarvis-{env_config.get('environment_file', 'default')}
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
{self._generate_volumes_yaml(volumes)}
    environment:
{self._generate_env_vars_yaml(environment_vars)}
    networks:
      - jarvis-network

networks:
  jarvis-network:
    driver: bridge
"""
    
    def _generate_systemd_service(self, service: str, env_config: Dict[str, Any]) -> str:
        """Generate systemd service file."""
        user = self.config["systemd"]["user"]
        group = self.config["systemd"]["group"]
        work_dir = self.config["systemd"]["working_directory"]
        restart = self.config["systemd"]["restart_policy"]
        
        return f"""[Unit]
Description=Jarvis {service.title()} Service
After=network.target

[Service]
Type=simple
User={user}
Group={group}
WorkingDirectory={work_dir}
Environment=PYTHONPATH={work_dir}
Environment=JARVIS_ENV={env_config.get('environment_file', '.env')}
ExecStart=/usr/bin/python3 {work_dir}/main.py --service={service}
Restart={restart}
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    def _generate_expose_ports(self) -> str:
        """Generate EXPOSE instructions for Dockerfile."""
        ports = self.config["docker"]["expose_ports"]
        return "\n".join(f"EXPOSE {port}" for port in ports)
    
    def _generate_volumes_yaml(self, volumes: List[str]) -> str:
        """Generate volumes section for docker-compose."""
        return "\n".join(f"      - {volume}" for volume in volumes)
    
    def _generate_env_vars_yaml(self, env_vars: List[str]) -> str:
        """Generate environment section for docker-compose."""
        return "\n".join(f"      - {var}" for var in env_vars)
    
    def _post_deployment_setup(self, environment: str, env_config: Dict[str, Any]):
        """Run post-deployment setup."""
        print("🔧 Running post-deployment setup...")
        
        deploy_env_dir = self.deploy_dir / environment
        
        # Create log rotation config
        logrotate_config = f"""
{deploy_env_dir}/logs/*.log {{
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 {os.getenv('USER', 'jarvis')} {os.getenv('USER', 'jarvis')}
}}
"""
        
        with open(deploy_env_dir / "logrotate.conf", 'w') as f:
            f.write(logrotate_config)
        
        # Create monitoring script
        monitor_script = deploy_env_dir / "monitor.sh"
        with open(monitor_script, 'w') as f:
            f.write(f"""#!/bin/bash
# Jarvis Monitoring Script

LOG_FILE="{deploy_env_dir}/logs/monitor.log"
PID_FILE="{deploy_env_dir}/jarvis.pid"

# Check if Jarvis is running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "$(date): Jarvis is running (PID: $PID)" >> $LOG_FILE
    else
        echo "$(date): Jarvis PID file exists but process not running" >> $LOG_FILE
        # Restart Jarvis
        cd {deploy_env_dir}
        ./start.sh
    fi
else
    echo "$(date): Jarvis is not running" >> $LOG_FILE
    # Start Jarvis
    cd {deploy_env_dir}
    ./start.sh
fi
""")
        
        monitor_script.chmod(0o755)
        
        print("✅ Post-deployment setup completed")
    
    def rollback(self, environment: str) -> bool:
        """Rollback deployment."""
        print(f"🔄 Rolling back {environment} deployment...")
        
        deploy_env_dir = self.deploy_dir / environment
        
        if not deploy_env_dir.exists():
            print(f"❌ No deployment found for {environment}")
            return False
        
        # Stop services
        if (deploy_env_dir / "stop.sh").exists():
            subprocess.run([str(deploy_env_dir / "stop.sh")], cwd=deploy_env_dir)
        
        # Remove deployment directory
        backup_dir = deploy_env_dir.parent / f"{environment}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        deploy_env_dir.rename(backup_dir)
        
        print(f"✅ Rolled back to backup: {backup_dir}")
        return True
    
    def status(self, environment: str) -> Dict[str, Any]:
        """Get deployment status."""
        deploy_env_dir = self.deploy_dir / environment
        
        if not deploy_env_dir.exists():
            return {"status": "not_deployed"}
        
        status_info = {
            "status": "deployed",
            "directory": str(deploy_env_dir),
            "services": {},
            "last_modified": datetime.fromtimestamp(deploy_env_dir.stat().st_mtime).isoformat()
        }
        
        # Check services
        if (deploy_env_dir / "start.sh").exists():
            # Check if processes are running
            try:
                result = subprocess.run(
                    ["pgrep", "-f", "python.*main.py"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    status_info["services"]["kernel"] = "running"
                    status_info["processes"] = len(result.stdout.strip().split('\n'))
                else:
                    status_info["services"]["kernel"] = "stopped"
                    
            except Exception:
                status_info["services"]["kernel"] = "unknown"
        
        return status_info

def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Jarvis Deployment Tool")
    parser.add_argument("action", choices=["deploy", "rollback", "status"], help="Action to perform")
    parser.add_argument("--environment", choices=["development", "staging", "production"], 
                       default="development", help="Target environment")
    parser.add_argument("--method", choices=["local", "docker", "systemd"], 
                       default="local", help="Deployment method")
    parser.add_argument("--config", default="deploy_config.json", help="Configuration file")
    
    args = parser.parse_args()
    
    deployer = JarvisDeployer(args.config)
    
    if args.action == "deploy":
        success = deployer.deploy(args.environment, args.method)
        sys.exit(0 if success else 1)
    elif args.action == "rollback":
        success = deployer.rollback(args.environment)
        sys.exit(0 if success else 1)
    elif args.action == "status":
        status = deployer.status(args.environment)
        print(json.dumps(status, indent=2))
        sys.exit(0)

if __name__ == "__main__":
    main()
