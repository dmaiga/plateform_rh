FROM python:3.13.3-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y curl build-essential gcc

COPY src/requirements.txt .
RUN uv pip install -r requirements.txt --system

# Copie tout le code y compris entrypoint.sh
COPY src/ .

# Donne les droits d’exécution après la copie
RUN chmod +x entrypoint.sh

EXPOSE 8000

CMD ["./entrypoint.sh"]
