import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Alert,
  AlertDescription,
} from "./ui-components";
import { AlertCircle } from "lucide-react";
import TradeHistory from "./dashboard/TradeHistory";
import BacktestForm from "./backtesting/BacktestForm";
import ResultsView from "./backtesting/ResultsView";

export const HistoryPage = () => {
  const [tradeHistory, setTradeHistory] = useState([]);
  const [backtestResults, setBacktestResults] = useState(null);
  const [isRunningBacktest, setIsRunningBacktest] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTradeHistory();
  }, []);

  const fetchTradeHistory = async () => {
    try {
      const response = await fetch("/api/trading/trades");
      if (!response.ok) throw new Error("Failed to fetch trade history");
      const data = await response.json();
      setTradeHistory(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch trade history",
      );
    }
  };

  const handleRunBacktest = async (config: any) => {
    try {
      setIsRunningBacktest(true);
      setError(null);

      const response = await fetch("/api/trading/backtest/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) throw new Error("Failed to run backtest");

      const results = await response.json();
      setBacktestResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run backtest");
    } finally {
      setIsRunningBacktest(false);
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <Alert className="" variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="">{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 gap-6">
        {/* Trade History */}
        <Card className="">
          <CardHeader className="">
            <CardTitle className="">Trade History</CardTitle>
          </CardHeader>
          <CardContent className="">
            <TradeHistory
              initialTrades={tradeHistory}
              onRefresh={fetchTradeHistory}
            />
          </CardContent>
        </Card>

        {/* Backtesting Section */}
        <Card className="">
          <CardHeader className="">
            <CardTitle className="">Backtesting</CardTitle>
          </CardHeader>
          <CardContent className="">
            {backtestResults ? (
              <ResultsView
                results={backtestResults}
                onReset={() => setBacktestResults(null)}
              />
            ) : (
              <BacktestForm
                onSubmit={handleRunBacktest}
                isSubmitting={isRunningBacktest}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
