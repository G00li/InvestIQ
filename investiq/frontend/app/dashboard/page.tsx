'use client';

import { useEffect, useState } from 'react';
import MarketAnalysis from '../components/MarketAnalysis';
import MarketSentiment from '../components/MarketSentiment';
import { Card, CardContent } from '../components/ui/card';

export default function DashboardPage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Dashboard de Mercado</h1>
      
      <Card className="mb-6 bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <p className="text-blue-800">
            <span className="font-semibold">Modo Demonstração:</span> Exibindo dados simulados para demonstração do projeto.
          </p>
        </CardContent>
      </Card>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <MarketAnalysis />
        <MarketSentiment />
      </div>
    </div>
  );
} 