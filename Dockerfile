FROM python:3.14-slim

WORKDIR /code

# Instala 'uv'
RUN pip install uv

# Copia o pyproject.toml (da raiz do build context)
COPY ./pyproject.toml /code/pyproject.toml

# Instala as dependências DENTRO do ambiente virtual
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-cache

# Copia o código da aplicação (a pasta 'app')
COPY ./app /code/app

# O uvicorn irá rodar a aplicação na porta 8000
EXPOSE 8000

# Comando para iniciar a aplicação (o módulo agora é 'app.main')
# Usa 'uv run' para executar dentro do ambiente virtual criado pelo uv sync
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]