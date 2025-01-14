"use client";
import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import {
  Alert,
  AlertTitle,
  AlertDescription,
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui-components";
import { ArrowUp, ArrowDown, RefreshCcw, AlertTriangle } from "lucide-react";

interface PriceData {
  timestamp: string;
  price: number;
  volume: number;
}

interface TradeData {
  symbol: string;
  type: "buy" | "sell";
  price: number;
  size: number;
  timestamp: string;
  status: "open" | "closed";
  pnl?: number;
}

const TradingView = () => {
  const [priceData, setPriceData] = useState<PriceData[]>([]);
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [activeTrades, setActiveTrades] = useState<TradeData[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch initial data and setup WebSocket connection
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        // Fetch historical price data
        const response = await fetch(
          "/api/trading/prices?symbol=BTC-USD&interval=1m",
        );
        const data = await response.json();
        setPriceData(data);

        // Setup WebSocket connection for real-time updates
        const ws = new WebSocket("ws://localhost:8000/ws/prices");

        ws.onopen = () => {
          setIsConnected(true);
          setError(null);
        };

        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          setCurrentPrice(data.price);
          setPriceData((prevData) => [
            ...prevData.slice(-99),
            {
              timestamp: data.timestamp,
              price: data.price,
              volume: data.volume,
            },
          ]);
        };

        ws.onerror = () => {
          setError("WebSocket connection error");
          setIsConnected(false);
        };

        ws.onclose = () => {
          setIsConnected(false);
        };

        return () => {
          ws.close();
        };
      } catch (err) {
        setError("Failed to fetch price data");
      }
    };

    fetchInitialData();
  }, []);

  // Fetch active trades
  useEffect(() => {
    const fetchActiveTrades = async () => {
      try {
        const response = await fetch("/api/trading/trades/active");
        const data = await response.json();
        setActiveTrades(data);
      } catch (err) {
        console.error("Failed to fetch active trades:", err);
      }
    };

    fetchActiveTrades();
    const interval = setInterval(fetchActiveTrades, 5000);

    return () => clearInterval(interval);
  }, []);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(price);
  };

  const getPriceChangeColor = (price: number, prevPrice: number) => {
    if (price > prevPrice) return "text-green-500";
    if (price < prevPrice) return "text-red-500";
    return "text-gray-500";
  };

  return (
    <div className="space-y-4">
      {/* Connection Status */}
      {!isConnected && (
        <Alert className="" variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle className="">Disconnected</AlertTitle>
          <AlertDescription className="">
            Lost connection to trading server. Attempting to reconnect...
          </AlertDescription>
        </Alert>
      )}

      {/* Price Chart */}
      <Card className="w-full">
        <CardHeader className="">
          <CardTitle className="flex items-center justify-between">
            <span>BTC/USD</span>
            {currentPrice && (
              <span
                className={getPriceChangeColor(
                  currentPrice,
                  priceData[priceData.length - 2]?.price || currentPrice,
                )}
              >
                {formatPrice(currentPrice)}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="">
          <div className="h-96">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={priceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(timestamp) => {
                    return new Date(timestamp).toLocaleTimeString();
                  }}
                />
                <YAxis
                  domain={["auto", "auto"]}
                  tickFormatter={(value) => formatPrice(value)}
                />
                <Tooltip
                  formatter={(value) => formatPrice(Number(value))}
                  labelFormatter={(label) => new Date(label).toLocaleString()}
                />
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke="#2563eb"
                  dot={false}
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Active Trades */}
      <Card className="">
        <CardHeader className="">
          <CardTitle className="">Active Trades</CardTitle>
        </CardHeader>
        <CardContent className="">
          <div className="space-y-4">
            {activeTrades.map((trade) => (
              <div
                key={trade.timestamp}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center space-x-4">
                  {trade.type === "buy" ? (
                    <ArrowUp className="text-green-500" />
                  ) : (
                    <ArrowDown className="text-red-500" />
                  )}
                  <div>
                    <p className="font-medium">{trade.symbol}</p>
                    <p className="text-sm text-gray-500">
                      {formatPrice(trade.price)} × {trade.size}
                    </p>
                  </div>
                </div>
                {trade.pnl && (
                  <span
                    className={
                      trade.pnl >= 0 ? "text-green-500" : "text-red-500"
                    }
                  >
                    {trade.pnl >= 0 ? "+" : ""}
                    {formatPrice(trade.pnl)}
                  </span>
                )}
              </div>
            ))}
            {activeTrades.length === 0 && (
              <p className="text-center text-gray-500">No active trades</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Trading Controls */}
      <div className="flex space-x-4">
        <Button
          variant="default"
          className="w-full"
          onClick={() => {
            /* Open buy order form */
          }}
        >
          Buy BTC
        </Button>
        <Button
          variant="outline"
          className="w-full"
          onClick={() => {
            /* Open sell order form */
          }}
        >
          Sell BTC
        </Button>
      </div>
    </div>
  );
};

export default TradingView;
