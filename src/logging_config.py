"""
Configuração de logging estruturado em JSON para FastAPI.

Este módulo fornece um formatter customizado que serializa logs em JSON,
preservando campos trace_id e span_id injetados pelo OpenTelemetry.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

from src.config import settings


class JSONFormatter(logging.Formatter):
    """
    Formatter customizado que serializa logs em formato JSON.
    
    Preserva campos adicionais passados via 'extra' dict e inclui
    informações de contexto como trace_id e span_id quando disponíveis.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formata o log record em JSON estruturado.
        
        Args:
            record: Log record a ser formatado.
            
        Returns:
            String JSON com o log formatado.
        """
        # Campos base do log
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.service_name,
        }
        
        # Adicionar trace_id e span_id se disponíveis (injetados pelo OpenTelemetry)
        if hasattr(record, "otelTraceID"):
            log_data["trace_id"] = record.otelTraceID
        if hasattr(record, "otelSpanID"):
            log_data["span_id"] = record.otelSpanID
        
        # Adicionar informações de localização do código
        log_data["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }
        
        # Adicionar campos extras passados via extra dict
        # Ignora campos internos do logging
        ignored_keys = {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "message", "pathname", "process", "processName", "relativeCreated",
            "thread", "threadName", "exc_info", "exc_text", "stack_info",
            "otelTraceID", "otelSpanID", "otelTraceSampled", "otelServiceName"
        }
        
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in ignored_keys and not key.startswith("_")
        }
        
        if extra_fields:
            log_data["extra"] = extra_fields
        
        # Adicionar exception info se presente
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Serializar para JSON
        return json.dumps(log_data, ensure_ascii=False, default=str)


def setup_logging(level: str = "INFO") -> None:
    """
    Configura o sistema de logging com formato JSON estruturado.
    
    Esta função deve ser chamada uma única vez no início da aplicação,
    antes de configurar o OpenTelemetry LoggingInstrumentor.
    
    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    # Obter o root logger
    root_logger = logging.getLogger()
    
    # Limpar handlers existentes para evitar duplicação
    root_logger.handlers.clear()
    
    # Criar handler para stdout
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    
    # Configurar nível de log
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    handler.setLevel(log_level)
    
    # Adicionar handler ao root logger
    root_logger.addHandler(handler)
    
    # Configurar loggers de bibliotecas para serem menos verbosos
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

