import logging
import json
import sys
import os
from datetime import datetime
import colorlog

class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings for logs.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno
        }
        
        if hasattr(record, "event"):
            log_record["event"] = record.event
            
        if hasattr(record, "command"):
            log_record["command"] = record.command
            
        if hasattr(record, "status"):
            log_record["status"] = record.status

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)

def setup_logger(name="Jarvis", config=None):
    """
    Sets up a structured logger with JSON file output and colored console output.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) # Catch all, filter by handler
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console Handler (Human Readable / Colored)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.get('logging', {}).get('level', 'INFO').upper(), logging.INFO) if config else logging.INFO)
    
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s%(reset)s",
        datefmt="%H:%M:%S",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler (JSON Structured)
    log_file = config.get('logging', {}).get('file', 'logs/jarvis.json') if config else "logs/jarvis.json"
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG) # Log full details to file
    file_formatter = JsonFormatter()
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

# Singleton access
_logger = None

def get_logger():
    global _logger
    if _logger is None:
        # Fallback if setup hasn't been called
        _logger = setup_logger()
    return _logger
