---
name: python-logging
description: >
  Guía para Python logging. Configuración, formatters, handlers, niveles.
  Trigger: Cuando se modifica logger_config.py o se agrega logging al proyecto.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Proyecto usa logging
- Se necesita debugging
- Configurar niveles de log (DEBUG, INFO, WARNING, ERROR)
- Agregar logging a nuevos módulos

## Logger Config de Este Proyecto

```python
# utils/logger_config.py
import logging
import sys

def setup_logger(name: str = None, level=logging.INFO):
    """Setup logger with console handler."""
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Add handler
    logger.addHandler(console_handler)
    
    return logger
```

## Usage

```python
# En cada módulo
import logging
logger = logging.getLogger(__name__)

# Setup (en main.py o al inicio)
from utils.logger_config import setup_logger
setup_logger(__name__)

# Niveles de logging
logger.debug("Debug info - solo en DEBUG")
logger.info("Info general")
logger.warning("Warning - algo no ideal")
logger.error("Error - algo falló")
logger.critical("Critical - fallo grave")
```

## Logging Levels

| Level | Value | When to use |
|-------|-------|-------------|
| DEBUG | 10 | Development, detailed info |
| INFO | 20 | Normal operation |
| WARNING | 30 | Something unexpected but handled |
| ERROR | 31 | Serious problem, function failed |
| CRITICAL | 50 | Program may crash |

## Structured Logging (JSON)

```python
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Usage
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

## Config with dictConfig

```python
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "standard",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "": {"level": "DEBUG", "handlers": ["console", "file"]}
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

## Best Practices

1. **Usar `__name__`** → Identifica el módulo
2. **No usar print()** → Siempre logger
3. **No loggear datos sensibles** → Passwords, tokens
4. **Niveles apropiados** → No todo en DEBUG
5. **Context** → Agregar user_id, transaction_id

## Logging con Contexto

```python
import logging

# Usar LoggerAdapter para contexto
class ContextLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return f"[{self.extra.get('user_id', 'N/A')}] {msg}", kwargs

logger = ContextLogger(logging.getLogger(__name__), {"user_id": "user123"})
logger.info("User performed action")
```

## Commands

```bash
# Test logging level
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
logging.debug('Test debug')
"

# Run with DEBUG
DEBUG=1 python main.py
```

## Resources

- **Docs**: https://docs.python.org/3/library/logging.html
- **Howto**: https://docs.python.org/3/howto/logging.html
- **Cookbook**: https://docs.python.org/3/howto/logging-cookbook.html
