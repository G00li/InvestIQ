from celery import Celery
import os
from dotenv import load_dotenv
import json
from datetime import datetime, UTC
import hashlib
import redis

# Carregando variáveis de ambiente
load_dotenv()

# Inicializar o Celery
celery_app = Celery(
    'market_tasks', 
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/1'
)

# Configurações do Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=600,  # 10 minutos
    task_soft_time_limit=540,  # 9 minutos
)

# Singleton para o cliente Redis
class RedisClient:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
        return cls._instance

# Tarefas Celery
@celery_app.task(name="analyze_market_task")
def analyze_market_task(ticker=None):
    """
    Tarefa Celery para analisar o mercado de forma assíncrona
    """
    from app.services.market_analysis_crew import MarketAnalysisCrew
    
    try:
        # Importando aqui para evitar circular imports
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        crew = MarketAnalysisCrew(OPENAI_API_KEY)
        
        # Função síncrona para chamar o Ollama
        result = crew.call_ollama_sync(ticker)
        
        # Salvar o resultado no Redis com um ID único
        task_id = hashlib.md5(f"{ticker}:{datetime.now(UTC).isoformat()}".encode()).hexdigest()
        redis_client = RedisClient.get_instance()
        redis_client.setex(f"task_result:{task_id}", 3600, json.dumps(result))
        
        return {"task_id": task_id, "status": "completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)} 