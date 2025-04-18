import { NextRequest, NextResponse } from 'next/server';
import { marketAnalysisFallback, marketSentimentFallback } from '../../utils/fallbackData';

// Define um timeout mais curto para as requisições
const TIMEOUT = 60 * 1000; // 60 segundos

// Cache para armazenar as últimas respostas bem-sucedidas
let apiCache: Record<string, { data: any, timestamp: number }> = {};

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  const path = params.path.join('/');
  
  try {
    // Em ambiente Docker, sempre usamos dados de fallback até resolvermos o problema de rede
    console.log(`Usando dados de fallback para ${path}`);
    
    if (path === 'market-analysis') {
      return NextResponse.json(marketAnalysisFallback);
    } else if (path === 'market-sentiment') {
      return NextResponse.json(marketSentimentFallback);
    }
    
    return NextResponse.json({ message: "API route not found", fallback: true });
  } catch (error) {
    console.error(`Erro ao processar requisição para ${path}:`, error);
    
    // Resposta de erro com fallback
    if (path === 'market-analysis') {
      return NextResponse.json(marketAnalysisFallback);
    } else if (path === 'market-sentiment') {
      return NextResponse.json(marketSentimentFallback);
    }
    
    // Resposta de erro genérica
    return NextResponse.json(
      { error: 'Falha ao processar requisição', fallback: true },
      { status: 200 } // Retornando 200 para evitar erros no frontend
    );
  }
} 