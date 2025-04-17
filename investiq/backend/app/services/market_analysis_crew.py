from crewai import Agent, Task, Crew
from langchain_community.llms import Ollama
from typing import Dict, List
import os
from time import sleep
from datetime import datetime, UTC

class MarketAnalysisCrew:
    def __init__(self, openai_api_key: str = None):
        self.llm = Ollama(
            model="ollama/orca-mini",
            base_url="http://localhost:11434",
            temperature=0.5,
        )

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

    def analyze_market(self) -> Dict:
        """
        Executa a análise de mercado usando o CrewAI com Ollama
        """
        try:
            agents = self.create_agents()
            tasks = self.create_tasks(agents)

            crew = Crew(
                agents=agents,
                tasks=tasks,
                verbose=True,
                max_round_time=60  # Tempo máximo por rodada em segundos
            )

            result = crew.kickoff()

            # Processando o resultado para separar as análises
            analysis_parts = result.split("Relatório")
            analysis_dict = {
                "market": analysis_parts[1].split("de notícias")[0].strip(),
                "news_sentiment": "Relatório de notícias" + analysis_parts[2].strip()
            }

            return {
                "analysis": {
                    **analysis_dict,
                    "timestamp": datetime.now(UTC).isoformat()
                },
                "status": "success"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao analisar mercado: {str(e)}",
                "error": str(e)
            } 