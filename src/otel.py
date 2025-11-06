"""
Configuração do OpenTelemetry para instrumentação automática de aplicações FastAPI.

Este módulo configura traces, métricas e logs usando OpenTelemetry SDK.
Deve ser importado antes de qualquer outro módulo da aplicação.
"""

import os
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

    # Configurar logging estruturado em JSON ANTES do OpenTelemetry
    # Isso garante que o formato JSON seja preservado
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    setup_logging(level=log_level)
    
    # Aplicar a instrumentação de log para injetar TraceID e SpanID
    # O LoggingInstrumentor adiciona campos otelTraceID e otelSpanID aos log records
    LoggingInstrumentor().instrument(set_logging_format=False)  # Não sobrescrever nosso formato

    # Aplicar as instrumentações automáticas
    # Instrumenta a aplicação FastAPI para métricas e traces
    FastAPIInstrumentor.instrument_app(app)
    # Instrumenta a biblioteca 'requests' para propagar o trace
    RequestsInstrumentor().instrument()

