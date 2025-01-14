"use client";
import React, { useState, useEffect } from "react";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui-components";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import { TrendingUp, TrendingDown, DollarSign, Activity } from "lucide-react";

interface PerformanceMetricsProps {
  interval?: "1d" | "1w" | "1m" | "3m" | "6m" | "1y";
  onIntervalChange?: (interval: string) => void;
}

interface PerformanceData {
  totalPnl: number;
  dailyPnl: number;
  winRate: number;
  totalTrades: number;
  averageProfitPerTrade: number;
  maxDrawdown: number;
  sharpeRatio: number;
  profitFactor: number;
}

interface ChartData {
  timestamp: string;
  value: number;
}

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({
  interval = "1w",
  onIntervalChange,
}) => {
  const [performanceData, setPerformanceData] =
    useState<PerformanceData | null>(null);
  const [equityCurve, setEquityCurve] = useState<ChartData[]>([]);
  const [dailyReturns, setDailyReturns] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPerformanceData = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `/api/trading/performance?interval=${interval}`,
        );
        const data = await response.json();
        setPerformanceData(data.metrics);
        setEquityCurve(data.equityCurve);
        setDailyReturns(data.dailyReturns);
      } catch (error) {
        console.error("Failed to fetch performance data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchPerformanceData();
    // Set up periodic refresh
    const refreshInterval = setInterval(fetchPerformanceData, 60000); // Refresh every minute

    return () => clearInterval(refreshInterval);
  }, [interval]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  if (loading || !performanceData) {
    return (
      <div className="w-full h-96 flex items-center justify-center">
        <div className="animate-pulse text-gray-400">
          Loading performance metrics...
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <DollarSign
                className={
                  performanceData.totalPnl >= 0
                    ? "text-green-500"
                    : "text-red-500"
                }
              />
              <div>
                <p className="text-sm font-medium text-gray-500">Total P&L</p>
                <p className="text-2xl font-bold">
                  {formatCurrency(performanceData.totalPnl)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Activity className="text-blue-500" />
              <div>
                <p className="text-sm font-medium text-gray-500">Win Rate</p>
                <p className="text-2xl font-bold">
                  {formatPercentage(performanceData.winRate)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <TrendingDown className="text-red-500" />
              <div>
                <p className="text-sm font-medium text-gray-500">
                  Max Drawdown
                </p>
                <p className="text-2xl font-bold">
                  {formatPercentage(performanceData.maxDrawdown)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <TrendingUp className="text-green-500" />
              <div>
                <p className="text-sm font-medium text-gray-500">
                  Sharpe Ratio
                </p>
                <p className="text-2xl font-bold">
                  {performanceData.sharpeRatio.toFixed(2)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts and Detailed Metrics */}
      <Card className="">
        <CardHeader className="">
          <div className="flex justify-between items-center">
            <CardTitle className="">Performance Analysis</CardTitle>
            <div className="flex space-x-2">
              {["1d", "1w", "1m", "3m", "6m", "1y"].map((i) => (
                <button
                  key={i}
                  onClick={() => onIntervalChange?.(i)}
                  className={`px-3 py-1 rounded-md text-sm ${
                    interval === i
                      ? "bg-primary text-primary-foreground"
                      : "text-gray-500 hover:bg-gray-100"
                  }`}
                >
                  {i.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent className="">
          <Tabs defaultValue="equity" className="w-full">
            <TabsList className="">
              <TabsTrigger className="" value="equity" selected={false}>
                Equity Curve
              </TabsTrigger>
              <TabsTrigger className="" value="returns" selected={false}>
                Daily Returns
              </TabsTrigger>
            </TabsList>

            <TabsContent className="" value="equity">
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={equityCurve}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) =>
                        new Date(value).toLocaleDateString()
                      }
                    />
                    <YAxis tickFormatter={(value) => formatCurrency(value)} />
                    <Tooltip
                      formatter={(value: number) => [
                        formatCurrency(value),
                        "Equity",
                      ]}
                      labelFormatter={(label) =>
                        new Date(label).toLocaleString()
                      }
                    />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#2563eb"
                      dot={false}
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </TabsContent>

            <TabsContent className="" value="returns">
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={dailyReturns}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) =>
                        new Date(value).toLocaleDateString()
                      }
                    />
                    <YAxis tickFormatter={(value) => `${value}%`} />
                    <Tooltip
                      formatter={(value: number) => [
                        `${value.toFixed(2)}%`,
                        "Return",
                      ]}
                      labelFormatter={(label) =>
                        new Date(label).toLocaleString()
                      }
                    />
                    <Bar dataKey="value" fill="#2563eb" name="Daily Return" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Detailed Metrics */}
      <Card className="">
        <CardHeader className="">
          <CardTitle className="">Detailed Metrics</CardTitle>
        </CardHeader>
        <CardContent className="">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="space-y-2">
              <p className="text-sm text-gray-500">Total Trades</p>
              <p className="text-lg font-medium">
                {performanceData.totalTrades}
              </p>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-gray-500">Average Profit per Trade</p>
              <p className="text-lg font-medium">
                {formatCurrency(performanceData.averageProfitPerTrade)}
              </p>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-gray-500">Profit Factor</p>
              <p className="text-lg font-medium">
                {performanceData.profitFactor.toFixed(2)}
              </p>
            </div>
            <div className="space-y-2">
              <p className="text-sm text-gray-500">Daily P&L</p>
              <p
                className={`text-lg font-medium ${
                  performanceData.dailyPnl >= 0
                    ? "text-green-500"
                    : "text-red-500"
                }`}
              >
                {formatCurrency(performanceData.dailyPnl)}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PerformanceMetrics;
