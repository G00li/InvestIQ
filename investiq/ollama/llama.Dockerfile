FROM ubuntu:22.04

# Instalar dependências essenciais
RUN apt-get update && \
    apt-get install -y curl ca-certificates --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Instalar Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Copiar o script de inicialização
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expor a porta do Ollama
EXPOSE 11434

# Configurações do Ollama
ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_MODELS=/root/.ollama/models
ENV OLLAMA_MEMORY_LIMIT=4096

# Iniciar o Ollama
CMD ["/entrypoint.sh"] 