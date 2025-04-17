from exa_py import Exa
from typing import Dict, List
import json

class MarketSentimentAnalyzer:
    def __init__(self, exa_api_key: str):
        self.exa = Exa(exa_api_key)

    async def get_market_sentiment(self, market_terms: List[str] = None) -> Dict:
        """
        Analisa o sentimento do mercado usando Exa.ai
        """
        if not market_terms:
            market_terms = ["financial markets", "stock market trends", "market analysis"]

        results = []
        for term in market_terms:
            search_results = self.exa.search(
                term,
                num_results=5,
                use_autoprompt=True
            )
            
            # Processando os resultados da pesquisa
            for result in search_results.results:
                results.append({
                    "title": result.title,
                    "url": result.url,
                    "published_date": result.published_date if hasattr(result, 'published_date') else None,
                    "author": result.author if hasattr(result, 'author') else None,
                })

        # Obtendo um resumo dos resultados usando o Exa
        summary = self.exa.search(
            "summarize recent market sentiment and trends",
            use_autoprompt=True,
            num_results=1
        )

        return {
            "sentiment_analysis": {
                "results": results,
                "summary": summary.results[0].text if summary.results else "No summary available"
            },
            "status": "success"
        } 