#!/bin/bash
set -e

echo "Iniciando o serviço Ollama..."
ollama serve &
OLLAMA_PID=$!

# Verificar se o Ollama está em execução
echo "Aguardando o Ollama iniciar..."
for i in {1..30}; do
  if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Ollama está em execução!"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "Timeout: Ollama não iniciou no tempo esperado."
    exit 1
  fi
  sleep 1
done

# Verificar e baixar o modelo llama2 se necessário
if ! ollama list | grep -q "llama2"; then
  echo "Baixando o modelo llama2..."
  ollama pull llama2
  echo "Modelo llama2 baixado com sucesso!"
else
  echo "Modelo llama2 já está disponível."
fi

# Pré-aquecer o modelo para carregar na memória
echo "Pré-aquecendo o modelo llama2..."
curl -s -X POST http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Olá, este é um teste para carregar o modelo. Responda com uma palavra.",
  "stream": false,
  "options": {
    "num_predict": 10
  }
}' > /dev/null

echo "Modelo Llama2 pré-aquecido e pronto para uso!"

# Manter o container em execução
echo "Ollama está pronto para uso na porta 11434!"
wait $OLLAMA_PID 