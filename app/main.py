import logging
import os
import time
import requests
from fastapi import FastAPI, HTTPException

# --- Configuração do OpenTelemetry (Bootstrapping) ---
# Importante: Isso deve rodar ANTES de importar o FastAPI e outros módulos instrumentados

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Configurar o Resource com o nome do serviço
resource = Resource.create({
    "service.name": os.environ.get("OTEL_SERVICE_NAME", "poc-fastapi-service"),
})

# Obter o endpoint do OTLP (gRPC usa a porta 4317)
# Se OTEL_EXPORTER_OTLP_ENDPOINT estiver definido como HTTP, convertemos para gRPC
otlp_endpoint_env = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318")
# Converter HTTP endpoint para gRPC (porta 4317)
# gRPC não usa http://, apenas o host:port
if otlp_endpoint_env.startswith("http://"):
    otlp_endpoint = otlp_endpoint_env.replace("http://", "").replace(":4318", ":4317")
elif otlp_endpoint_env.startswith("https://"):
    otlp_endpoint = otlp_endpoint_env.replace("https://", "").replace(":4318", ":4317")
else:
    # Se já estiver no formato host:port, usar diretamente (assumindo porta 4317 se não especificada)
    otlp_endpoint = otlp_endpoint_env if ":" in otlp_endpoint_env else f"{otlp_endpoint_env}:4317"

# Configurar o TracerProvider para traces
trace_provider = TracerProvider(resource=resource)
# Desabilitar SSL/TLS para conexão não criptografada com o collector
otlp_trace_exporter = OTLPSpanExporter(
    endpoint=otlp_endpoint,
    insecure=True  # Desabilita SSL/TLS
)
trace_provider.add_span_processor(BatchSpanProcessor(otlp_trace_exporter))
trace.set_tracer_provider(trace_provider)

# Configurar o MeterProvider para métricas
# Desabilitar SSL/TLS para conexão não criptografada com o collector
otlp_metric_exporter = OTLPMetricExporter(
    endpoint=otlp_endpoint,
    insecure=True  # Desabilita SSL/TLS
)
metric_reader = PeriodicExportingMetricReader(otlp_metric_exporter, export_interval_millis=5000)
metrics_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
metrics.set_meter_provider(metrics_provider)

# 1. Configuração básica de logging
logging.basicConfig(level=logging.INFO)
# Aplicar a instrumentação de log para injetar TraceID e SpanID
LoggingInstrumentor().instrument(set_logging_format=True)

logger = logging.getLogger(__name__)

# 2. Inicialização da aplicação FastAPI
app = FastAPI()

# 3. Aplicar as instrumentações automáticas
# Instrumenta o FastAPI para métricas e traces
FastAPIInstrumentor.instrument_app(app)
# Instrumenta a biblioteca 'requests' para propagar o trace
RequestsInstrumentor().instrument()

# --- Fim da Configuração do OpenTelemetry ---


# --- Endpoints da Aplicação ---

@app.get("/")
def read_root():
    """ Endpoint raiz simples """
    logger.info("Acessando o endpoint raiz.")
    return {"status": "ok", "service": os.environ.get("OTEL_SERVICE_NAME", "unknown")}

@app.get("/simular-financiamento")
def simular_financiamento():
    """
    Endpoint de negócio que simula a complexidade do nosso domínio
    (financiamento imobiliário).
    """
    logger.info("Iniciando simulação de financiamento...")

    try:
        # 1. Simula trabalho interno (ex: cálculos de taxa)
        time.sleep(0.1)

        # 2. Simula chamada a um serviço externo (ex: bureau de crédito ou API de taxas)
        # O 'RequestsInstrumentor' vai capturar isso automaticamente
        logger.info("Consultando serviço externo de taxas (simulado)...")
        # Usamos o httpbin para simular uma API externa
        try:
            response = requests.get("https://httpbin.org/delay/0.15", timeout=5)
            response.raise_for_status() # Garante que temos um erro se a API falhar
            taxa_externa_ms = response.elapsed.total_seconds() * 1000
        except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
            logger.warning(f"Serviço externo indisponível: {e}. Usando valor simulado.")
            # Se o serviço externo falhar, usamos um valor simulado para continuar o fluxo
            taxa_externa_ms = 150.0  # Valor simulado

        # 3. Simula mais trabalho (ex: formatação da proposta)
        time.sleep(0.05)

        logger.info("Simulação concluída com sucesso.")
        return {
            "proposta_status": "aprovada", 
            "taxa_externa_ms": taxa_externa_ms,
            "observacao": "Valor simulado" if taxa_externa_ms == 150.0 else None
        }

    except Exception as e:
        logger.error(f"Falha na simulação: {e}", exc_info=True)
        # Retorna um erro HTTP apropriado em vez de fazer raise genérico
        raise HTTPException(status_code=500, detail=f"Erro interno na simulação: {str(e)}")