"""
Configuração centralizada de variáveis de ambiente usando Pydantic Settings.

Este módulo fornece uma instância singleton de Settings que lê variáveis
de ambiente do arquivo .env ou do ambiente, com validação automática e
type safety.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """
    Configurações da aplicação carregadas de variáveis de ambiente.
    
    As variáveis podem ser definidas em:
    1. Arquivo .env na raiz do projeto
    2. Variáveis de ambiente do sistema
    3. Valores padrão definidos abaixo
    
    Ordem de precedência: variáveis de ambiente > .env > defaults
    """
    
    service_name: str = Field(
        default="poc-fastapi-service",
        alias="OTEL_SERVICE_NAME",
        description="Nome do serviço para OpenTelemetry"
    )
    
    otel_exporter_otlp_endpoint: str = Field(
        default="http://otel-collector:4318",
        alias="OTEL_EXPORTER_OTLP_ENDPOINT",
        description="Endpoint do OpenTelemetry Collector (HTTP)"
    )
    
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Nível de log da aplicação"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def get_grpc_endpoint(self) -> str:
        """
        Converte endpoint HTTP para gRPC (porta 4318 -> 4317).
        
        O OpenTelemetry Collector expõe:
        - HTTP na porta 4318
        - gRPC na porta 4317
        
        Este método converte o endpoint HTTP para o formato gRPC necessário
        pelos exporters OTLP.
        
        Returns:
            Endpoint gRPC no formato host:port (sem http://)
        """
        endpoint = self.otel_exporter_otlp_endpoint
        
        if endpoint.startswith("http://"):
            endpoint = endpoint.replace("http://", "").replace(":4318", ":4317")
        elif endpoint.startswith("https://"):
            endpoint = endpoint.replace("https://", "").replace(":4318", ":4317")
        else:
            # Se já estiver no formato host:port, usar diretamente
            # Assumir porta 4317 se não especificada
            endpoint = endpoint if ":" in endpoint else f"{endpoint}:4317"
        
        return endpoint


# Singleton: instância global para uso em toda a aplicação
# Esta instância é criada uma única vez e reutilizada em todos os módulos
settings = Settings()

