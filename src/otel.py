"""
Configuração do OpenTelemetry para instrumentação automática de aplicações FastAPI.

Este módulo configura traces, métricas e logs usando OpenTelemetry SDK.
Deve ser importado antes de qualquer outro módulo da aplicação.
"""

from fastapi import FastAPI

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

from src.config import settings
from src.logging_config import setup_logging


def setup_telemetry(app: FastAPI) -> None:
    """
    Configura OpenTelemetry e instrumenta uma aplicação FastAPI existente.
    
    Esta função deve ser chamada uma única vez no início da aplicação,
    após a criação da instância do FastAPI.
    
    Args:
        app: Instância do FastAPI a ser instrumentada.
    """
    # Configurar o Resource com o nome do serviço
    resource = Resource.create({
        "service.name": settings.service_name,
    })

    # Obter o endpoint gRPC (conversão automática de HTTP para gRPC)
    otlp_endpoint = settings.get_grpc_endpoint()

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

    # Configurar logging estruturado em JSON ANTES do OpenTelemetry
    # Isso garante que o formato JSON seja preservado
    setup_logging(level=settings.log_level)
    
    # Aplicar a instrumentação de log para injetar TraceID e SpanID
    # O LoggingInstrumentor adiciona campos otelTraceID e otelSpanID aos log records
    LoggingInstrumentor().instrument(set_logging_format=False)  # Não sobrescrever nosso formato

    # Aplicar as instrumentações automáticas
    # Instrumenta a aplicação FastAPI para métricas e traces
    FastAPIInstrumentor.instrument_app(app)
    # Instrumenta a biblioteca 'requests' para propagar o trace
    RequestsInstrumentor().instrument()

