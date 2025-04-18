from fastapi import FastAPI, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from app.services.market_analysis_crew import MarketAnalysisCrew
from app.services.market_sentiment_exa import MarketSentimentAnalyzer
from typing import List, Optional, Dict
from redis import asyncio as aioredis
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from datetime import datetime, UTC
import time
import requests
from urllib.parse import urlparse
import asyncio
from app.celery_app import celery_app
import json
from redis import Redis

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
async def get_market_analysis(ticker: Optional[str] = None, quick: Optional[str] = "true"):
    """
    Endpoint para obter análise de mercado
    
    Parâmetros:
    - ticker: Opcional. Se fornecido, a análise focará neste ticker específico
    - quick: Opcional. Se "true" (padrão), utiliza análise rápida. Se "false", utiliza CrewAI
    """
    try:
        # Converter o parâmetro 'quick' para booleano
        use_quick_analysis = quick.lower() == "true" if quick else True
        
        print(f"Endpoint /api/market-analysis chamado com ticker={ticker}, quick={quick}, use_quick_analysis={use_quick_analysis}")
        
        if use_quick_analysis:
            # Análise rápida (padrão)
            print("Usando modo de análise rápida")
            analysis = await market_crew.quick_analyze_market(ticker)
        else:
            # Análise completa usando CrewAI (mais lenta)
            print("Usando modo de análise completa com CrewAI")
            analysis = await market_crew.analyze_market(ticker)
        
        print(f"Análise concluída com status: {analysis.get('status')}")
        
        if analysis.get("status") == "error":
            error_msg = analysis.get("message", "Erro no serviço de análise de mercado")
            print(f"Erro na análise: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=error_msg
            )
        
        return analysis
    except Exception as e:
        error_msg = f"Erro ao executar análise de mercado: {str(e)}"
        print(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=error_msg
        )

@app.get("/api/market-analysis-async")
async def get_market_analysis_async(ticker: Optional[str] = None, background_tasks: BackgroundTasks = None):
    """
    Endpoint para iniciar uma análise de mercado assíncrona usando Celery
    
    Parâmetros:
    - ticker: Opcional. Se fornecido, a análise focará neste ticker específico
    """
    try:
        # Verificar o cache antes de iniciar uma nova tarefa
        redis_client = Redis(host='redis', port=6379, db=0, decode_responses=True)
        cache_key = f"analysis:sync:{ticker}" if ticker else "analysis:sync:general"
        
        cached_result = await app.state.redis.get(cache_key)
        if cached_result:
            print(f"Encontrado resultado em cache para tarefa assíncrona de {ticker}")
            return json.loads(cached_result)
            
        # Iniciar uma tarefa Celery
        task = celery_app.send_task(
            "analyze_market_task",
            args=[ticker],
            kwargs={}
        )
        
        # Fornecer um resultado parcial imediato enquanto processa em background
        current_time = datetime.now(UTC).isoformat()
        
        return {
            "task_id": task.id,
            "status": "processing",
            "analysis": {
                "market": f"Análise de {ticker or 'mercado'} em andamento. Seu ID de tarefa é {task.id}",
                "news_sentiment": "Aguarde alguns instantes e consulte o status no endpoint /api/task-status/{task_id}",
                "ticker": ticker,
                "timestamp": current_time,
                "method": "async"
            },
            "polling_url": f"/api/task-status/{task.id}",
            "estimated_time": "60-120 segundos",
            "message": "Análise em andamento. Use o endpoint /api/task-status/{task_id} para verificar o status e obter o resultado."
        }
    except Exception as e:
        error_msg = f"Erro ao iniciar análise assíncrona: {str(e)}"
        print(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=error_msg
        )

@app.get("/api/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Verifica o status de uma tarefa assíncrona
    
    Parâmetros:
    - task_id: ID da tarefa retornado pelo endpoint market-analysis-async
    """
    try:
        # Verificar o status da tarefa no Celery
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.ready():
            # Tarefa completa
            result = task_result.result
            
            # Se a tarefa retornou um task_id do Redis, buscar o resultado
            if isinstance(result, dict) and "task_id" in result and result.get("status") == "completed":
                redis = app.state.redis
                redis_task_id = result["task_id"]
                stored_result = await redis.get(f"task_result:{redis_task_id}")
                
                if stored_result:
                    return json.loads(stored_result)
                else:
                    return {
                        "status": "completed",
                        "message": "Análise concluída, mas o resultado não está mais disponível"
                    }
            
            # Caso contrário, retornar o resultado direto da tarefa
            return result
        else:
            # Tarefa ainda em processamento
            return {
                "task_id": task_id,
                "status": "processing",
                "message": "Análise ainda está em processamento"
            }
    except Exception as e:
        error_msg = f"Erro ao verificar status da tarefa: {str(e)}"
        print(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=error_msg
        )

@app.get("/api/market-analysis-crew")
async def get_market_analysis_crew(ticker: Optional[str] = None):
    """
    Endpoint para obter análise de mercado usando especificamente o CrewAI
    
    Parâmetros:
    - ticker: Opcional. Se fornecido, a análise focará neste ticker específico
    """
    try:
        # Log para debugging
        print(f"Iniciando análise CrewAI para ticker: {ticker}")
        
        # Forçando o uso da análise completa com CrewAI
        analysis = await market_crew.analyze_market(ticker)
        
        # Log do resultado
        print(f"Análise CrewAI concluída com status: {analysis.get('status')}")
        
        if analysis.get("status") == "error":
            error_msg = analysis.get("message", "Erro no serviço de análise de mercado")
            print(f"Erro na análise CrewAI: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=error_msg
            )
        
        return analysis
    except Exception as e:
        error_msg = f"Erro ao executar análise de mercado com CrewAI: {str(e)}"
        print(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=error_msg
        )

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

@app.get("/api/openai-status")
async def check_openai_status():
    """
    Verificar se o serviço OpenAI está disponível
    """
    try:
        # Verificar se a chave da API OpenAI está configurada
        if not OPENAI_API_KEY:
            return {
                "status": "error",
                "message": "Chave da API OpenAI não configurada",
                "timestamp": datetime.now(UTC).isoformat()
            }
        
        # Verificar se o serviço OpenAI está respondendo
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            "https://api.openai.com/v1/models", 
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            models = response.json().get("data", [])
            available_models = [model["id"] for model in models if "gpt" in model["id"]]
            
            return {
                "status": "up",
                "message": "Serviço OpenAI está operacional",
                "models": available_models[:5],  # Limitando a 5 modelos para brevidade
                "timestamp": datetime.now(UTC).isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"Serviço OpenAI respondeu com código {response.status_code}: {response.text}",
                "timestamp": datetime.now(UTC).isoformat()
            }
    except Exception as e:
        return {
            "status": "down",
            "message": f"Serviço OpenAI não está acessível: {str(e)}",
            "timestamp": datetime.now(UTC).isoformat()
        }

@app.get("/api/ollama-status")
async def check_ollama_status():
    """
    Verificar se o serviço Ollama está disponível
    """
    try:
        # Consultar o serviço Ollama no container dedicado
        response = requests.get("http://ollama:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            return {
                "status": "up",
                "message": "Serviço Ollama está operacional",
                "models": response.json().get("models", []),
                "timestamp": datetime.now(UTC).isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"Serviço Ollama respondeu com código {response.status_code}",
                "timestamp": datetime.now(UTC).isoformat()
            }
    except Exception as e:
        return {
            "status": "down",
            "message": f"Serviço Ollama não está acessível: {str(e)}",
            "timestamp": datetime.now(UTC).isoformat()
        }
