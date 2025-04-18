import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Skeleton } from '../components/ui/skeleton';
import { marketAnalysisFallback } from '../utils/fallbackData';

interface MarketAnalysisData {
  status: string;
  analysis: {
    market: string;
    news_sentiment: string;
    timestamp: string;
  };
}

export default function MarketAnalysis() {
  const [data, setData] = useState<MarketAnalysisData | null>(null);
  const [loading, setLoading] = useState(true);

  // Usando dados de demonstração diretamente
  useEffect(() => {
    // Simulando um pequeno carregamento para demonstração
    const timer = setTimeout(() => {
      console.log('Carregando dados de demonstração para análise de mercado');
      setData(marketAnalysisFallback);
      setLoading(false);
    }, 800); // Pequeno delay para simular carregamento

    return () => clearTimeout(timer);
  }, []);

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Análise de Mercado</CardTitle>
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
        <CardTitle>Análise de Mercado</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold mb-2">Análise Técnica e Fundamental</h3>
            <p className="text-gray-600">{data?.analysis.market}</p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Análise de Notícias e Sentimento</h3>
            <p className="text-gray-600">{data?.analysis.news_sentiment}</p>
          </div>
          <div className="text-sm text-gray-400">
            Atualizado em: {new Date(data?.analysis.timestamp || '').toLocaleString('pt-BR')}
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 