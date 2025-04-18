export const marketAnalysisFallback = {
  status: "success",
  analysis: {
    market: "O mercado está demonstrando uma tendência de lateralização após um período de queda. Os principais índices mostram sinais de indecisão, com volumes reduzidos. O suporte atual está em um nível crítico de teste.",
    news_sentiment: "As notícias recentes têm mostrado uma mistura de sentimentos, com preocupações sobre inflação sendo parcialmente compensadas por resultados corporativos positivos. A incerteza permanece, mas há sinais iniciais de melhora no sentimento dos investidores.",
    timestamp: new Date().toISOString()
  }
};

export const marketSentimentFallback = {
  status: "success",
  sentiment_analysis: {
    summary: "O sentimento de mercado atual é neutro com leve viés positivo. Notícias sobre política monetária, resultados corporativos e indicadores econômicos têm influenciado as expectativas dos investidores.",
    results: [
      {
        title: "Bancos centrais sinalizam possível pausa no ciclo de alta de juros",
        url: "https://example.com/news/1",
        published_date: new Date().toISOString(),
        author: "Análise Econômica"
      },
      {
        title: "Resultados trimestrais superam expectativas no setor de tecnologia",
        url: "https://example.com/news/2",
        published_date: new Date().toISOString(),
        author: "Tech Finance"
      },
      {
        title: "Dados de emprego mostram resiliência da economia",
        url: "https://example.com/news/3",
        published_date: new Date().toISOString(),
        author: "Economic Observer"
      }
    ]
  }
}; 