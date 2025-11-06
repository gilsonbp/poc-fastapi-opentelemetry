# 🚀 POC: Stack de Observabilidade Completa com OpenTelemetry

> **⚠️ Este é um projeto de Prova de Conceito (POC)**  
> Este repositório serve como referência para implementar uma stack completa de observabilidade (métricas, logs e traces) usando OpenTelemetry, similar ao New Relic, mas com ferramentas open-source.

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura](#-arquitetura)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Execução](#-instalação-e-execução)
- [Como Usar em Outros Projetos](#-como-usar-em-outros-projetos)
- [Acessando as Interfaces](#-acessando-as-interfaces)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Visão Geral

Esta POC demonstra como implementar uma stack completa de observabilidade para aplicações FastAPI, incluindo:

- ✅ **Métricas** (Prometheus)
- ✅ **Logs Estruturados em JSON** (Loki + Promtail) com correlação automática via TraceID/SpanID
- ✅ **Traces Distribuídos** (Tempo)
- ✅ **Visualização Unificada** (Grafana)
- ✅ **Alertas** (Alertmanager)
- ✅ **Correlação** entre métricas, logs e traces
- ✅ **Middleware HTTP** para logging automático de requisições

A stack é totalmente containerizada com Docker Compose e pronta para uso em desenvolvimento ou como base para produção.

---

## 🏗️ Arquitetura

```
┌─────────────────┐
│  FastAPI App    │
│  (Instrumentado)│
└────────┬────────┘
         │ OTLP (gRPC/HTTP)
         ▼
┌─────────────────┐
│ OTel Collector  │◄─── Recebe telemetria
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌─────────┐ ┌──────┐ ┌────────┐ ┌──────────┐
│Prometheus│ │ Tempo│ │  Loki  │ │  Debug  │
│(Métricas)│ │(Traces)│ │ (Logs) │ │  (Log)  │
└────┬────┘ └──────┘ └────┬───┘ └──────────┘
     │                    │
     │                    │
     ▼                    ▼
┌─────────────────────────────────┐
│         Grafana                 │
│  (Visualização Unificada)       │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Alertmanager    │
│   (Alertas)     │
└─────────────────┘
```

### Fluxo de Dados

1. **Aplicação FastAPI** envia telemetria (traces, métricas) via OTLP para o **OpenTelemetry Collector**
2. **Aplicação FastAPI** gera logs estruturados em JSON (com TraceID/SpanID injetados automaticamente)
3. **OTel Collector** processa e roteia os dados:
   - **Traces** → Tempo
   - **Métricas** → Prometheus (via endpoint `/metrics`)
4. **Promtail** coleta logs dos containers Docker (formato JSON) → **Loki**
5. **Grafana** consome todos os dados para visualização unificada com correlação automática
6. **Prometheus** avalia regras de alerta e envia para **Alertmanager**

---

## 🛠️ Tecnologias Utilizadas

| Componente | Tecnologia | Função |
|------------|------------|--------|
| **Aplicação** | FastAPI + Python 3.14 | API REST instrumentada |
| **Instrumentação** | OpenTelemetry SDK | Geração de telemetria |
| **Coletor** | OpenTelemetry Collector | Hub central de telemetria |
| **Métricas** | Prometheus | Armazenamento e query de métricas |
| **Logs** | Loki + Promtail | Agregação e coleta de logs |
| **Traces** | Tempo | Armazenamento de traces distribuídos |
| **Visualização** | Grafana | Dashboards e correlação |
| **Alertas** | Alertmanager | Gerenciamento de alertas |

---

## 📦 Pré-requisitos

- **Docker** >= 20.10
- **Docker Compose** >= 2.0
- **Python** >= 3.14 (apenas para desenvolvimento local, não necessário para Docker)
- **uv** (gerenciador de pacotes Python) - instalado automaticamente no Dockerfile

---

## 🚀 Instalação e Execução

### 1. Clone o repositório

```bash
git clone <seu-repositorio>
cd poc-fastapi-otel
```

### 2. Execute a stack completa

```bash
docker compose up --build
```

Este comando irá:
- Construir a imagem da aplicação FastAPI
- Iniciar todos os serviços (Prometheus, Grafana, Tempo, Loki, etc.)
- Configurar automaticamente os data sources no Grafana

### 3. Aguarde a inicialização

Aguarde alguns segundos para todos os serviços iniciarem. Você pode verificar o status com:

```bash
docker compose ps
```

### 4. Teste a aplicação

```bash
# Endpoint raiz
curl http://localhost:8000/

# Endpoint de exemplo (simula financiamento)
curl http://localhost:8000/simular-financiamento
```

### 5. Parar a stack

```bash
docker compose down
```

Para remover também os volumes (dados persistentes):

```bash
docker compose down -v
```

---

## 🔄 Como Usar em Outros Projetos

### Passo 1: Adicionar Dependências OpenTelemetry

No seu `pyproject.toml` ou `requirements.txt`, adicione:

```toml
dependencies = [
    "opentelemetry-distro>=0.59b0",
    "opentelemetry-sdk>=1.38.0",
    "opentelemetry-exporter-otlp>=1.38.0",
    "opentelemetry-instrumentation-fastapi>=0.59b0",
    "opentelemetry-instrumentation-logging>=0.59b0",
    "opentelemetry-instrumentation-requests>=0.59b0",
    # ... suas outras dependências
]
```

### Passo 2: Instrumentar sua Aplicação

**Opção A: Estrutura modular (recomendado)**

Copie os módulos de configuração de `src/`:

1. **`logging_config.py`** - Configura logging estruturado em JSON
2. **`otel.py`** - Configura OpenTelemetry (traces, métricas)
3. **`middleware.py`** - Middleware para logging automático de requisições HTTP

No seu arquivo principal (`main.py`):

```python
from fastapi import FastAPI
from otel import setup_telemetry
from middleware import HTTPLoggingMiddleware

# Criar aplicação FastAPI
app = FastAPI(
    title="Minha Aplicação",
    description="Aplicação instrumentada com OpenTelemetry",
    version="1.0.0"
)

# Instrumentar com OpenTelemetry (configura logging JSON + traces + métricas)
setup_telemetry(app)

# Adicionar middleware de logging HTTP
app.add_middleware(HTTPLoggingMiddleware)

# Seus endpoints aqui
@app.get("/")
def root():
    return {"status": "ok"}
```

**Benefícios desta estrutura:**
- Logs estruturados em JSON com correlação automática via TraceID/SpanID
- Logging automático de todas requisições HTTP (método, path, status, duração, IP, user agent)
- Filtragem inteligente de health checks
- Contexto de negócio pode ser adicionado via `extra` dict nos logs

**Opção B: Configuração inline**

Se preferir tudo no mesmo arquivo, configure o OpenTelemetry antes de criar os endpoints, mas após criar a instância do FastAPI.

### Passo 3: Configurar Variáveis de Ambiente

No seu `docker-compose.yml`, adicione as variáveis de ambiente:

```yaml
services:
  sua-aplicacao:
    environment:
      - OTEL_SERVICE_NAME=seu-servico-nome
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
    depends_on:
      - otel-collector
```

### Passo 4: Copiar Arquivos de Configuração

Copie os seguintes diretórios/arquivos para seu projeto:

```
├── docker-compose.yml          # Adicione os serviços de observabilidade
├── otel/
│   └── otel-collector-config.yml
├── prometheus/
│   ├── prometheus.yml
│   └── alerts.yml
├── tempo/
│   └── tempo.yml
├── loki/                       # (opcional, se usar Loki)
├── promtail/
│   └── promtail.yml
├── alertmanager/
│   └── alertmanager.yml
└── grafana/
    └── provisioning/
        └── datasources/
            └── datasources.yml
```

### Passo 5: Ajustar Nome do Serviço

No `docker-compose.yml`, atualize o nome do serviço da sua aplicação e ajuste as dependências do `otel-collector` se necessário.

### Passo 6: Executar

```bash
docker compose up --build
```

---

## 🌐 Acessando as Interfaces

Após iniciar a stack, acesse:

| Serviço | URL | Credenciais | Descrição |
|---------|-----|-------------|-----------|
| **Grafana** | http://localhost:3000 | (sem login - anônimo habilitado) | Visualização unificada de métricas, logs e traces |
| **Prometheus** | http://localhost:9090 | - | Query de métricas e alertas |
| **Tempo** | http://localhost:3200 | - | API de traces (use Grafana para visualização) |
| **Loki** | http://localhost:3100 | - | API de logs (use Grafana para visualização) |
| **Alertmanager** | http://localhost:9093 | - | Gerenciamento de alertas |
| **FastAPI App** | http://localhost:8000 | - | Aplicação principal |
| **FastAPI Docs** | http://localhost:8000/docs | - | Documentação Swagger |

### Usando o Grafana

1. **Explorar Métricas:**
   - Vá em **Explore** → Selecione **Prometheus**
   - Digite queries como: `http_server_duration_milliseconds_count`

2. **Explorar Logs:**
   - Vá em **Explore** → Selecione **Loki**
   - Use queries como: `{service="app-fastapi"}` ou `{container="poc-fastapi-otel-app-fastapi-1"}`
   - Filtre por nível: `{container="..."} |= "level":"ERROR"`
   - Busque por trace_id: `{container="..."} |= "trace_id":"abc123..."`
   - Os logs são estruturados em JSON, facilitando queries e correlação com traces

3. **Explorar Traces:**
   - Vá em **Explore** → Selecione **Tempo**
   - Use busca simples: `{ service.name = "poc-fastapi-service" }`
   - Ou cole um TraceID diretamente

4. **Correlação:**
   - Ao visualizar um trace, você pode clicar em spans para ver logs e métricas relacionados
   - Os data sources estão configurados para correlação automática

---

## 📁 Estrutura do Projeto

```
poc-fastapi-otel/
├── src/
│   ├── __init__.py
│   ├── main.py             # Aplicação FastAPI com endpoints
│   ├── otel.py             # Configuração OpenTelemetry
│   ├── logging_config.py   # Configuração de logging estruturado em JSON
│   └── middleware.py       # Middleware HTTP para logging automático
├── otel/
│   └── otel-collector-config.yml  # Configuração do OTel Collector
├── prometheus/
│   ├── prometheus.yml          # Configuração do Prometheus
│   └── alerts.yml              # Regras de alertas
├── tempo/
│   └── tempo.yml               # Configuração do Tempo
├── promtail/
│   └── promtail.yml            # Configuração do Promtail (coleta logs)
├── alertmanager/
│   └── alertmanager.yml        # Configuração do Alertmanager
├── grafana/
│   └── provisioning/
│       └── datasources/
│           └── datasources.yml # Data sources automáticos do Grafana
├── docker-compose.yml           # Orquestração de todos os serviços
├── Dockerfile                  # Build da aplicação FastAPI
├── pyproject.toml              # Dependências Python
└── README.md                  # Esta documentação
```

**Estrutura Modular:**
- `src/otel.py`: Configuração OpenTelemetry isolada e reutilizável
- `src/logging_config.py`: Formatter JSON customizado com suporte a TraceID/SpanID
- `src/middleware.py`: Middleware para logging automático de requisições HTTP
- `src/main.py`: Aplicação FastAPI focada apenas em endpoints

---

## 🔧 Troubleshooting

### Problema: "empty ring" no Grafana ao consultar traces

**Causa:** O Grafana está tentando executar queries de métricas de traces que ainda não foram geradas.

**Solução:**
1. Use busca simples de traces no Grafana (deixe o campo vazio ou use `{ service.name = "seu-servico" }`)
2. Aguarde 2-3 minutos após gerar traces para o `metrics_generator` do Tempo processar
3. Faça algumas requisições à aplicação para gerar mais dados:
   ```bash
   for i in {1..10}; do curl http://localhost:8000/simular-financiamento; done
   ```

### Problema: Traces não aparecem no Tempo

**Verificações:**
1. Verifique se o OTel Collector está recebendo dados:
   ```bash
   docker compose logs otel-collector | grep -i "traces"
   ```
2. Verifique se o Tempo está rodando:
   ```bash
   docker compose ps tempo
   curl http://localhost:3200/ready
   ```
3. Verifique se há traces no Tempo:
   ```bash
   curl "http://localhost:3200/api/search?limit=10"
   ```

### Problema: Métricas não aparecem no Prometheus

**Verificações:**
1. Verifique se o Prometheus está coletando do OTel Collector:
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```
2. Verifique se o endpoint de métricas do Collector está acessível:
   ```bash
   curl http://localhost:8889/metrics
   ```
3. No Prometheus UI, vá em **Status → Targets** e verifique se `otel-collector` está **UP**

### Problema: Logs não aparecem no Loki

**Verificações:**
1. Verifique se o Promtail está rodando:
   ```bash
   docker compose ps promtail
   ```
2. Verifique os logs do Promtail:
   ```bash
   docker compose logs promtail
   ```
3. Verifique se os logs da aplicação estão em formato JSON:
   ```bash
   docker compose logs app-fastapi --tail 5
   ```
   Você deve ver logs em formato JSON com campos como `trace_id`, `span_id`, `http`, etc.
4. No Grafana, use queries como:
   - `{container="poc-fastapi-otel-app-fastapi-1"}`
   - `{container="..."} |= "level":"ERROR"` (filtrar por nível)
   - `{container="..."} |= "trace_id":"abc123"` (buscar por trace_id)

### Problema: Erro "connection refused" ao enviar telemetria

**Causa:** A aplicação não consegue conectar ao OTel Collector.

**Solução:**
1. Verifique se o `otel-collector` está rodando:
   ```bash
   docker compose ps otel-collector
   ```
2. Verifique se a variável `OTEL_EXPORTER_OTLP_ENDPOINT` está correta no `docker-compose.yml`
3. Verifique se a aplicação está no mesmo network Docker que o collector (usando `depends_on`)

### Problema: Erro SSL/TLS ao enviar telemetria

**Causa:** O collector não está configurado para SSL.

**Solução:** Certifique-se de que `insecure=True` está configurado nos exporters (já está no código desta POC).

---

## 📚 Recursos Adicionais

- [Documentação OpenTelemetry](https://opentelemetry.io/docs/)
- [Documentação Prometheus](https://prometheus.io/docs/)
- [Documentação Grafana](https://grafana.com/docs/)
- [Documentação Tempo](https://grafana.com/docs/tempo/latest/)
- [Documentação Loki](https://grafana.com/docs/loki/latest/)

---

## 📝 Notas Importantes

- ⚠️ Esta é uma **POC para desenvolvimento**. Para produção, considere:
  - Configurar autenticação no Grafana
  - Habilitar SSL/TLS entre componentes
  - Configurar retenção de dados adequada
  - Implementar backup dos dados
  - Configurar notificações reais no Alertmanager (email, Slack, etc.)
  - Ajustar nível de log via variável `LOG_LEVEL` (DEBUG, INFO, WARNING, ERROR)

- 🔒 **Segurança:** O modo anônimo do Grafana está habilitado apenas para facilitar testes. Desabilite em produção.

- 💾 **Persistência:** Os dados são armazenados em volumes Docker. Use `docker compose down -v` com cuidado (remove todos os dados).

- 📝 **Logs Estruturados:** Os logs são gerados em formato JSON com:
  - Correlação automática via `trace_id` e `span_id` (injetados pelo OpenTelemetry)
  - Informações HTTP automáticas (método, path, status, duração, IP, user agent)
  - Contexto de negócio via `extra` dict
  - Filtragem automática de health checks (`/`, `/health`, `/docs`, etc.)

---

## 🤝 Contribuindo

Este é um projeto de referência. Sinta-se livre para adaptar e melhorar conforme suas necessidades!

---

## 📄 Licença

Este projeto é uma POC de referência e pode ser usado livremente como base para outros projetos.

