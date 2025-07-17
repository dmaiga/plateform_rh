FROM python:3.13.3-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Ajout de dépendances système nécessaires
RUN apt-get update && apt-get install -y curl build-essential gcc

# Copie des requirements et installation
COPY src/requirements.txt .
RUN uv pip install -r requirements.txt --system

# Copie du code source
COPY src/ .

EXPOSE 8000

CMD ["./entrypoint.sh"]
