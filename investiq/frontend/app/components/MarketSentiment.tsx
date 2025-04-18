import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { marketSentimentFallback } from '../utils/fallbackData';

interface SentimentResult {
  title: string;
  url: string;
  published_date: string | null;
  author: string | null;
}

interface MarketSentimentData {
  sentiment_analysis: {
    results: SentimentResult[];
    summary: string;
  };
  status: string;
}

export default function MarketSentiment() {
  const [data, setData] = useState<MarketSentimentData | null>(null);
  const [loading, setLoading] = useState(true);

  // Usando dados de demonstração diretamente
  useEffect(() => {
    // Simulando um pequeno carregamento para demonstração
    const timer = setTimeout(() => {
      console.log('Carregando dados de demonstração para sentimento de mercado');
      setData(marketSentimentFallback);
      setLoading(false);
    }, 1200); // Um pouco mais lento que o outro componente para simular carregamentos diferentes

    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Sentimento de Mercado</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-3/4" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Sentimento de Mercado</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div>
            <h3 className="font-semibold mb-2">Resumo do Sentimento</h3>
            <p className="text-gray-600">{data?.sentiment_analysis.summary}</p>
          </div>
          
          <div>
            <h3 className="font-semibold mb-4">Notícias Relevantes</h3>
            <div className="space-y-4">
              {data?.sentiment_analysis.results.map((result, index) => (
                <div key={index} className="border-b pb-4 last:border-b-0">
                  <a 
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline font-medium"
                  >
                    {result.title}
                  </a>
                  <div className="text-sm text-gray-500 mt-1">
                    {result.author && <span>Por {result.author} • </span>}
                    {result.published_date && (
                      <span>
                        {new Date(result.published_date).toLocaleDateString('pt-BR')}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 