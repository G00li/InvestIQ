#!/bin/bash

# Aguardar pelos serviços necessários
echo "Aguardando o serviço Ollama estar disponível..."
while ! curl -s http://ollama:11434/api/tags > /dev/null; do
  sleep 2
done
echo "Serviço Ollama está disponível!"

echo "Aguardando o serviço Redis estar disponível..."
while ! nc -z redis 6379; do
  sleep 2
done
echo "Serviço Redis está disponível!"

# Iniciar o worker do Celery em background
echo "Iniciando o worker do Celery..."
celery -A app.celery_app worker --loglevel=info --concurrency=2 &

# Iniciar o FastAPI
echo "Iniciando o servidor FastAPI..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload