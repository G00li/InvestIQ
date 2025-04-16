from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Adicionando CORS para permitir requisições do frontend (Next.js)
origins = [
    "http://localhost:3000",  # Next.js default local port
    "https://your-nextjs-domain.com",  # Seu domínio de produção
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Permite origens específicas
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos os headers
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI Backend"}

@app.get("/data")
def get_data():
    return {"data": "This is data from the FastAPI backend"}
