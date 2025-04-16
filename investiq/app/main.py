import os
from fastapi import FastAPI
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Busca a chave da OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")

# Verificação simples
if not openai_api_key:
    raise RuntimeError("🚨 A variável de ambiente OPENAI_API_KEY não foi encontrada!")

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Market AI Backenddd for InvestIQ"}
