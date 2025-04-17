#!/bin/bash

# Iniciar o Ollama em background
ollama serve &

# Aguardar o Ollama iniciar
sleep 5

# Iniciar o FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload