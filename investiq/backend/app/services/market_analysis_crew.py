from crewai import Agent, Task, Crew
from langchain_ollama import OllamaLLM
from langchain.llms.base import LLM
from langchain.schema import LLMResult
from typing import Dict, List, Optional, Any, Union, Mapping
import os
from time import sleep
from datetime import datetime, UTC, timedelta
import asyncio
import requests
import json
import redis
import hashlib
import httpx
import logging

# Singleton para o cliente Redis
class RedisClient:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
        return cls._instance

class CustomOllamaLLM(LLM):
    """Classe personalizada para interagir diretamente com a API do Ollama"""
    
    base_url: str = "http://ollama:11434"
    model: str = "ollama/llama2"  # Formato correto para o CrewAI
    temperature: float = 0.5
    request_timeout: int = 120  # Aumentado para 2 minutos
    max_retries: int = 3
    
    @property
    def _llm_type(self) -> str:
        return "custom_ollama"
        
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        """Chama a API do Ollama diretamente"""
        # Verificar cache primeiro
        cache_key = f"ollama:prompt:{hashlib.md5(prompt.encode()).hexdigest()}"
        redis_client = RedisClient.get_instance()
        cached_result = redis_client.get(cache_key)
        
        if cached_result:
            print(f"Resultado encontrado no cache")
            return cached_result
            
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "llama2",  # Aqui usamos apenas "llama2" pois é o formato que a API do Ollama espera
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": 1024,  # Limitar o tamanho da resposta
                "num_ctx": 2048  # Limitar o contexto para evitar problemas de memória
            }
        }
        
        if stop:
            data["options"]["stop"] = stop
        
        # Tentar com retries
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    headers=headers,
                    data=json.dumps(data),
                    timeout=self.request_timeout
                )
                
                if response.status_code != 200:
                    if attempt < self.max_retries:
                        sleep(2)  # Espera 2 segundos antes de tentar novamente
                        continue
                    raise ValueError(f"Erro na chamada à API do Ollama: {response.text}")
                    
                result = response.json()
                response_text = result.get("response", "")
                
                # Armazenar no cache por 1 hora
                if response_text:
                    redis_client.setex(cache_key, 3600, response_text)
                
                return response_text
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < self.max_retries:
                    sleep(2 * (attempt + 1))  # Backoff exponencial
                    continue
                return f"Timeout ao processar a requisição: {str(e)}"
            except Exception as e:
                if attempt < self.max_retries:
                    sleep(2)
                    continue
                return f"Erro ao processar a requisição: {str(e)}"

class MarketAnalysisCrew:
    def __init__(self, openai_api_key: str = None):
        # Usando a classe personalizada para evitar problemas com o LiteLLM
        self.llm = CustomOllamaLLM(
            model="ollama/llama2",  # Formato correto para o CrewAI
            base_url="http://ollama:11434",
            temperature=0.5,
        )
        self.ollama_url = "http://ollama:11434"
        self.redis_client = RedisClient.get_instance()

    async def check_ollama_connection(self) -> bool:
        """
        Verifica se o serviço Ollama está disponível
        """
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def create_agents(self) -> List[Agent]:
        market_analyst = Agent(
            role='Analista de Mercado',
            goal='Analisar aspectos técnicos e fundamentais do mercado',
            backstory="""Especialista em análise técnica e fundamental, com foco em 
            tendências de mercado, indicadores técnicos e cenário macroeconômico.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iterations=2  # Limitando o número de iterações
        )

        news_sentiment_analyst = Agent(
            role='Analista de Notícias e Sentimento',
            goal='Avaliar notícias e sentimento do mercado',
            backstory="""Especialista em análise de notícias e sentimento de mercado.
            Experiência em interpretar o impacto de eventos e o comportamento dos investidores.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False,
            max_iterations=2  # Limitando o número de iterações
        )

        return [market_analyst, news_sentiment_analyst]

    def create_tasks(self, agents: List[Agent]) -> List[Task]:
        market_analysis = Task(
            description="""
            Analise o mercado considerando:
            1. Tendência principal e níveis técnicos
            2. Indicadores econômicos importantes
            3. Cenário macroeconômico atual
            Seja muito conciso e direto.
            """,
            expected_output="""
            Relatório de mercado com:
            - Tendência e níveis técnicos
            - Indicadores principais
            - Cenário macro
            Máximo 3 linhas por tópico.
            """,
            agent=agents[0]
        )

        news_sentiment_analysis = Task(
            description="""
            Avalie notícias e sentimento:
            1. Principais eventos de mercado
            2. Nível de otimismo/pessimismo
            3. Impactos esperados
            Seja muito conciso e direto.
            """,
            expected_output="""
            Relatório de notícias e sentimento com:
            - Eventos principais
            - Humor do mercado
            - Impactos previstos
            Máximo 3 linhas por tópico.
            """,
            agent=agents[1]
        )

        return [market_analysis, news_sentiment_analysis]

    async def analyze_market(self, ticker: str = None) -> Dict:
        """
        Executa a análise de mercado usando o CrewAI com Ollama
        Opcionalmente pode receber um ticker específico para análise
        """
        try:
            # Verificando se Ollama está acessível
            if not await self.check_ollama_connection():
                return {
                    "status": "error",
                    "message": "Serviço Ollama não está disponível. Verifique se o serviço está em execução.",
                    "timestamp": datetime.now(UTC).isoformat()
                }
                
            try:
                # Modificando as descrições das tarefas se um ticker específico foi fornecido
                loop = asyncio.get_event_loop()
                agents = await loop.run_in_executor(None, self.create_agents)
                
                # Se um ticker específico foi fornecido, personaliza as tarefas
                if ticker:
                    tasks = await self.create_specific_tasks(agents, ticker)
                else:
                    tasks = await loop.run_in_executor(None, self.create_tasks, agents)
                
                # Configurar o Crew com menor tempo de execução
                crew = Crew(
                    agents=agents,
                    tasks=tasks,
                    verbose=True,
                    max_round_time=30  # Reduzido de 60 para 30 segundos
                )
                
                # Executar com timeout para evitar travamentos
                try:
                    # Definir um timeout para a operação completa
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, crew.kickoff),
                        timeout=60  # Timeout de 60 segundos para o processo inteiro
                    )
                except asyncio.TimeoutError:
                    return {
                        "analysis": {
                            "market": "Análise não completada devido a timeout. Por favor, tente novamente mais tarde.",
                            "news_sentiment": "Análise não completada devido a timeout. Por favor, tente novamente mais tarde.",
                            "ticker": ticker,
                            "timestamp": datetime.now(UTC).isoformat()
                        },
                        "status": "timeout"
                    }
                
                # Processando o resultado para separar as análises
                try:
                    analysis_parts = result.split("Relatório")
                    if len(analysis_parts) >= 3:
                        analysis_dict = {
                            "market": analysis_parts[1].split("de notícias")[0].strip(),
                            "news_sentiment": "Relatório de notícias" + analysis_parts[2].strip()
                        }
                    else:
                        analysis_dict = {
                            "market": result,
                            "news_sentiment": "Informações insuficientes para análise de sentimento"
                        }
                except Exception as e:
                    # Em caso de erro no processamento do resultado, retornar o resultado bruto
                    analysis_dict = {
                        "market": str(result)[:500],  # Limitando para não sobrecarregar a resposta
                        "raw_error": str(e)
                    }

                return {
                    "analysis": {
                        **analysis_dict,
                        "ticker": ticker,
                        "timestamp": datetime.now(UTC).isoformat()
                    },
                    "status": "success"
                }
            except Exception as e:
                raise Exception(f"Erro na execução do CrewAI: {str(e)}")
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao analisar mercado: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat()
            }
            
    async def create_specific_tasks(self, agents: List[Agent], ticker: str) -> List[Task]:
        """
        Cria tarefas específicas para analisar um ticker determinado
        """
        market_analysis = Task(
            description=f"""
            Analise o ticker {ticker} considerando:
            1. Tendência principal e níveis técnicos
            2. Indicadores econômicos importantes que afetam este ativo
            3. Perspectivas de curto e médio prazo
            Seja muito conciso e direto.
            """,
            expected_output=f"""
            Relatório de análise para {ticker}:
            - Tendência e níveis técnicos
            - Indicadores principais
            - Perspectivas futuras
            Máximo 3 linhas por tópico.
            """,
            agent=agents[0]
        )

        news_sentiment_analysis = Task(
            description=f"""
            Avalie notícias e sentimento para {ticker}:
            1. Principais eventos recentes relacionados a este ativo
            2. Nível de otimismo/pessimismo dos investidores
            3. Impactos esperados no curto prazo
            Seja muito conciso e direto.
            """,
            expected_output=f"""
            Relatório de notícias e sentimento para {ticker}:
            - Eventos principais
            - Humor do mercado
            - Impactos previstos
            Máximo 3 linhas por tópico.
            """,
            agent=agents[1]
        )

        return [market_analysis, news_sentiment_analysis]

    async def quick_analyze_market(self, ticker=None):
        try:
            # Verificar se há resultados em cache
            cache_key = f"market_analysis_{ticker}" if ticker else "market_analysis_general"
            cached_result = self.redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Prompt mais conciso para análise rápida
            if ticker:
                prompt = f"Faça uma análise rápida e direta do ticker {ticker}. Forneça apenas: 1) Tendência atual (alta/baixa/neutra), 2) Razão principal para essa tendência, 3) Uma recomendação simples (comprar/vender/manter). Máximo de 3 frases."
            else:
                prompt = "Faça uma análise rápida e direta do mercado geral hoje. Forneça apenas: 1) Tendência atual do mercado (alta/baixa/neutra), 2) Razão principal para essa tendência, 3) Um setor em destaque. Máximo de 3 frases."
            
            # Configurar tempo limite mais curto para respostas rápidas
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": "llama2",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": 150  # Limitar tamanho da resposta
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result.get("response", "").strip()
                    
                    # Salvar no cache por 15 minutos
                    response_data = {
                        "status": "success",
                        "data": {
                            "analysis": analysis,
                            "ticker": ticker if ticker else "general",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    self.redis_client.setex(cache_key, 15 * 60, json.dumps(response_data))
                    return response_data
                
                # Resposta em caso de erro
                return {
                    "status": "error",
                    "message": f"Erro na análise rápida: Código {response.status_code}",
                    "fallback_analysis": f"Não foi possível analisar {'o ticker ' + ticker if ticker else 'o mercado'} no momento. Tente novamente mais tarde ou use a análise assíncrona."
                }
        except Exception as e:
            logging.error(f"Erro em quick_analyze_market: {str(e)}")
            return {
                "status": "error",
                "message": f"Erro na análise rápida: {str(e)}",
                "fallback_analysis": f"Não foi possível analisar {'o ticker ' + ticker if ticker else 'o mercado'} no momento. Tente novamente mais tarde ou use a análise assíncrona."
            }

    def call_ollama_sync(self, ticker: str = None) -> Dict:
        """
        Versão síncrona da chamada ao Ollama para ser usada pelo Celery
        """
        try:
            # Verificar no cache primeiro
            redis_client = RedisClient.get_instance()
            cache_key = f"analysis:sync:{ticker}" if ticker else "analysis:sync:general"
            
            cached_result = redis_client.get(cache_key)
            if cached_result:
                print(f"Encontrado resultado em cache para {ticker} (sync)")
                return json.loads(cached_result)
            
            # Verificar conexão com Ollama
            try:
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                if response.status_code != 200:
                    return {
                        "status": "error",
                        "message": "Serviço Ollama não está disponível",
                        "timestamp": datetime.now(UTC).isoformat()
                    }
            except Exception:
                return {
                    "status": "error",
                    "message": "Não foi possível conectar ao serviço Ollama",
                    "timestamp": datetime.now(UTC).isoformat()
                }
            
            # Criando o prompt com base no ticker
            if ticker:
                prompt = f"""
                Por favor, forneça uma análise concisa do ticker {ticker} com:
                
                1. Tendência principal e níveis técnicos importantes.
                2. Indicadores econômicos relevantes que afetam este ativo.
                3. Perspectivas para este ativo no curto e médio prazo.
                
                Forneça também uma análise de notícias e sentimento de mercado para {ticker}:
                1. Principais eventos recentes.
                2. Humor atual do mercado em relação a este ativo.
                3. Possíveis impactos no preço.
                
                Estruture sua resposta em dois blocos: 'Análise Técnica e Fundamental' e 'Notícias e Sentimento'.
                """
            else:
                prompt = """
                Por favor, forneça uma análise concisa do mercado atual com:
                
                1. Tendência principal dos principais índices (S&P 500, Nasdaq, etc.).
                2. Indicadores econômicos relevantes e seu impacto atual.
                3. Perspectivas para o mercado no curto e médio prazo.
                
                Forneça também uma análise de notícias e sentimento geral de mercado:
                1. Principais eventos recentes que impactam os mercados.
                2. Humor atual dos investidores.
                3. Possíveis impactos nas próximas semanas.
                
                Estruture sua resposta em dois blocos: 'Análise Técnica e Fundamental' e 'Notícias e Sentimento'.
                """
            
            # Chamada direta ao LLM
            try:
                llm = CustomOllamaLLM(
                    model="ollama/llama2",
                    base_url="http://ollama:11434",
                    temperature=0.5,
                    request_timeout=180  # 3 minutos para processamento síncrono
                )
                
                result = llm._call(prompt)
                
                # Dividindo a resposta
                parts = result.split("Notícias e Sentimento")
                
                # Se conseguiu dividir corretamente
                if len(parts) >= 2:
                    market_analysis = parts[0].replace("Análise Técnica e Fundamental", "").strip()
                    news_sentiment = "Notícias e Sentimento" + parts[1].strip()
                else:
                    # Caso contrário, tenta encontrar outra divisão possível
                    market_analysis = result[:len(result)//2]
                    news_sentiment = result[len(result)//2:]
                
                # Montar o resultado
                analysis_result = {
                    "analysis": {
                        "market": market_analysis,
                        "news_sentiment": news_sentiment,
                        "ticker": ticker,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "method": "sync",
                        "cached": False
                    },
                    "status": "success"
                }
                
                # Salvar no cache por 1 hora (3600 segundos)
                redis_client.setex(cache_key, 3600, json.dumps(analysis_result))
                
                return analysis_result
                
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Erro ao processar análise síncrona: {str(e)}",
                    "timestamp": datetime.now(UTC).isoformat()
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao executar análise síncrona: {str(e)}",
                "timestamp": datetime.now(UTC).isoformat()
            } 