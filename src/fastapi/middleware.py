"""
Middleware para logging automático de requisições HTTP no FastAPI.

Este módulo fornece um middleware que captura e loga informações
sobre requisições HTTP, incluindo métricas de performance e contexto.
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


logger = logging.getLogger(__name__)


class HTTPLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware que loga informações sobre requisições HTTP.
    
    Captura métricas de performance, informações da requisição e resposta,
    e integra automaticamente com TraceID/SpanID do OpenTelemetry.
    """
    
    def __init__(
        self, 
        app: ASGIApp,
        skip_paths: set[str] = None
    ):
        """
        Inicializa o middleware.
        
        Args:
            app: Aplicação ASGI.
            skip_paths: Conjunto de paths para não logar (ex: health checks).
        """
        super().__init__(app)
        self.skip_paths = skip_paths or {"/", "/health", "/docs", "/redoc", "/openapi.json"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Processa a requisição e loga informações ao finalizar.
        
        Args:
            request: Requisição HTTP.
            call_next: Próximo handler na cadeia.
            
        Returns:
            Response HTTP.
        """
        # Pular logging para paths configurados
        if request.url.path in self.skip_paths:
            return await call_next(request)
        
        # Capturar tempo de início
        start_time = time.time()
        
        # Processar requisição
        response = await call_next(request)
        
        # Calcular duração
        duration_ms = (time.time() - start_time) * 1000
        
        # Extrair informações da requisição
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Construir contexto estruturado para o log
        log_context = {
            "http": {
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params) if request.query_params else None,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_host,
                "user_agent": user_agent,
            }
        }
        
        # Determinar nível de log baseado no status code
        if response.status_code >= 500:
            log_level = logging.ERROR
            message = f"{request.method} {request.url.path} - {response.status_code} (Erro no servidor)"
        elif response.status_code >= 400:
            log_level = logging.WARNING
            message = f"{request.method} {request.url.path} - {response.status_code} (Erro do cliente)"
        else:
            log_level = logging.INFO
            message = f"{request.method} {request.url.path} - {response.status_code}"
        
        # Logar com contexto estruturado
        logger.log(
            log_level,
            message,
            extra=log_context
        )
        
        return response

