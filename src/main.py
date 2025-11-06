"""
Aplicação FastAPI de exemplo com OpenTelemetry.

Este módulo contém os endpoints da aplicação e utiliza a configuração
OpenTelemetry definida em otel.py.
"""

import logging
import os
import time
import requests
from fastapi import FastAPI, HTTPException

from src.otel import setup_telemetry
from src.middleware import HTTPLoggingMiddleware

# Criar aplicação FastAPI
app = FastAPI(
    title="POC FastAPI + OpenTelemetry",
    description="Exemplo de aplicação FastAPI instrumentada com OpenTelemetry",
    version="0.1.0"
)

# Configurar telemetria (instrumenta o app criado acima)
setup_telemetry(app)

# Adicionar middleware de logging HTTP
app.add_middleware(HTTPLoggingMiddleware)

logger = logging.getLogger(__name__)


# --- Endpoints da Aplicação ---

@app.get("/")
def read_root():
    """Endpoint raiz simples para health check."""
    # Health check - log mínimo (já filtrado pelo middleware)
    return {"status": "ok", "service": os.environ.get("OTEL_SERVICE_NAME", "unknown")}


@app.get("/simular-financiamento")
def simular_financiamento():
    """
    Endpoint de negócio que simula a complexidade do nosso domínio
    (financiamento imobiliário).
    
    Simula:
    - Processamento interno (cálculos)
    - Chamada a serviço externo (API de taxas)
    - Tratamento de erros
    """
    logger.info(
        "Iniciando simulação de financiamento",
        extra={"event": "simulation_started"}
    )

    try:
        # 1. Simula trabalho interno (ex: cálculos de taxa)
        time.sleep(0.1)

        # 2. Simula chamada a um serviço externo (ex: bureau de crédito ou API de taxas)
        # O 'RequestsInstrumentor' vai capturar isso automaticamente
        logger.info(
            "Consultando serviço externo de taxas",
            extra={"external_service": "httpbin", "event": "external_call"}
        )
        # Usamos o httpbin para simular uma API externa
        try:
            response = requests.get("https://httpbin.org/delay/0.15", timeout=5)
            response.raise_for_status()  # Garante que temos um erro se a API falhar
            taxa_externa_ms = response.elapsed.total_seconds() * 1000
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            logger.warning(
                "Serviço externo indisponível - usando valor simulado",
                extra={
                    "external_service": "httpbin",
                    "error": str(e),
                    "fallback": True,
                    "event": "external_call_failed"
                }
            )
            # Se o serviço externo falhar, usamos um valor simulado para continuar o fluxo
            taxa_externa_ms = 150.0  # Valor simulado

        # 3. Simula mais trabalho (ex: formatação da proposta)
        time.sleep(0.05)

        proposta_status = "aprovada"
        observacao = "Valor simulado" if taxa_externa_ms == 150.0 else None

        logger.info(
            "Simulação concluída com sucesso",
            extra={
                "event": "simulation_completed",
                "business": {
                    "proposta_status": proposta_status,
                    "taxa_externa_ms": round(taxa_externa_ms, 2),
                    "observacao": observacao
                }
            }
        )
        
        return {
            "proposta_status": proposta_status,
            "taxa_externa_ms": taxa_externa_ms,
            "observacao": observacao
        }

    except Exception as e:
        logger.error(
            "Falha na simulação",
            extra={
                "event": "simulation_failed",
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        # Retorna um erro HTTP apropriado em vez de fazer raise genérico
        raise HTTPException(status_code=500, detail=f"Erro interno na simulação: {str(e)}")

