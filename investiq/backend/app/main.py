from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from app.services.market_analysis_crew import MarketAnalysisCrew
from app.services.market_sentiment_exa import MarketSentimentAnalyzer
from typing import List, Optional
from redis import asyncio as aioredis
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from datetime import datetime, UTC
import time

# Carregando variáveis de ambiente
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis = aioredis.from_url("redis://redis", encoding="utf-8", decode_responses=True)
    app.state.redis = redis
    yield
    # Shutdown
    await redis.close()

app = FastAPI(lifespan=lifespan)

# Configurando CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Obtendo as chaves de API do ambiente
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")

# Inicializando os serviços
market_crew = MarketAnalysisCrew(OPENAI_API_KEY)
market_sentiment = MarketSentimentAnalyzer(EXA_API_KEY)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    redis = request.app.state.redis
    
    # 5 requests per minute
    requests = await redis.incr(f"rate_limit:{client_ip}")
    await redis.expire(f"rate_limit:{client_ip}", 60)
    
    if requests > 5:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"}
        )
    
    response = await call_next(request)
    return response

@app.get("/api/market-analysis")
async def get_market_analysis():
    """
    Endpoint para obter análise de mercado usando CrewAI
    """
    try:
        analysis = market_crew.analyze_market()
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-sentiment")
async def get_market_sentiment(terms: Optional[List[str]] = None):
    """
    Endpoint para obter sentimento de mercado usando Exa.ai
    """
    try:
        sentiment = await market_sentiment.get_market_sentiment(terms)
        return sentiment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def check_redis_connection():
    try:
        redis = aioredis.from_url("redis://redis", encoding="utf-8", decode_responses=True)
        await redis.ping()
        await redis.close()
        return True
    except Exception:
        return False

async def check_external_apis():
    try:
        # Verifica se as chaves de API estão configuradas
        if not OPENAI_API_KEY or not EXA_API_KEY:
            return False
        return True
    except Exception:
        return False

@app.get("/health")
async def health_check():
    """
    Verifica a saúde da aplicação e suas dependências
    """
    redis_ok = await check_redis_connection()
    apis_ok = await check_external_apis()
    
    health_status = {
        "status": "healthy" if redis_ok and apis_ok else "unhealthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "services": {
            "redis": "up" if redis_ok else "down",
            "external_apis": "configured" if apis_ok else "misconfigured"
        }
    }
    
    if not redis_ok or not apis_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )
    
    return health_status

# ... resto do seu código existente ... 