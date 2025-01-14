import React from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Alert,
  AlertDescription,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
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
  Legend,
} from "recharts";
import {
  AlertCircle,
  TrendingUp,
  TrendingDown,
  DollarSign,
  BarChart2,
} from "lucide-react";

interface Trade {
  timestamp: string;
  type: "buy" | "sell";
  entryPrice: number;
  exitPrice: number;
  size: number;
  pnl: number;
  returnPercent: number;
  duration: number;
}

interface PerformanceMetrics {
  totalReturn: number;
  annualizedReturn: number;
  sharpeRatio: number;
  sortinoRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  totalTrades: number;
  averageTradeReturn: number;
  averageWinningTrade: number;
  averageLosingTrade: number;
  largestWin: number;
  largestLoss: number;
  averageDuration: number;
}

interface BacktestResults {
  equityCurve: { timestamp: string; equity: number; drawdown: number }[];
  monthlyReturns: { month: string; return: number }[];
  trades: Trade[];
  metrics: PerformanceMetrics;
  error?: string;
}

interface ResultsViewProps {
  results: BacktestResults;
  isLoading?: boolean;
  onReset: () => void;
}

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const formatPercent = (value: number) => {
  return `${value.toFixed(2)}%`;
};

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString();
};

const ResultsView: React.FC<ResultsViewProps> = ({
  results,
  isLoading = false,
  onReset,
}) => {
  if (isLoading) {
    return (
      <Card className="">
        <CardContent className="">
          <div className="flex items-center justify-center h-64">
            <span className="text-gray-500">Loading backtest results...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (results.error) {
    return (
      <Alert className="" variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription className="">{results.error}</AlertDescription>
      </Alert>
    );
  }

  const metrics = results.metrics;

  return (
    <div className="space-y-6">
      {/* Key Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <DollarSign
                className={
                  metrics.totalReturn >= 0 ? "text-green-500" : "text-red-500"
                }
              />
              <div>
                <p className="text-sm text-gray-500">Total Return</p>
                <p className="text-2xl font-bold">
                  {formatPercent(metrics.totalReturn)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="">
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <BarChart2 className="text-blue-500" />
              <div>
                <p className="text-sm text-gray-500">Sharpe Ratio</p>
                <p className="text-2xl font-bold">
                  {metrics.sharpeRatio.toFixed(2)}
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
                <p className="text-sm text-gray-500">Max Drawdown</p>
                <p className="text-2xl font-bold">
                  {formatPercent(metrics.maxDrawdown)}
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
                <p className="text-sm text-gray-500">Win Rate</p>
                <p className="text-2xl font-bold">
                  {formatPercent(metrics.winRate)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Analysis Tabs */}
      <Tabs className="" defaultValue="equity">
        <TabsList className="">
          <TabsTrigger className="" value="equity" selected={false}>
            Equity Curve
          </TabsTrigger>
          <TabsTrigger className="" value="monthly" selected={false}>
            Monthly Returns
          </TabsTrigger>
          <TabsTrigger className="" value="trades" selected={false}>
            Trade History
          </TabsTrigger>
          <TabsTrigger className="" value="metrics" selected={false}>
            Detailed Metrics
          </TabsTrigger>
        </TabsList>

        <TabsContent className="" value="equity">
          <Card className="">
            <CardHeader className="">
              <CardTitle className="">Equity Curve</CardTitle>
            </CardHeader>
            <CardContent className="">
              <div className="h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={results.equityCurve}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="timestamp"
                      tickFormatter={(value) =>
                        new Date(value).toLocaleDateString()
                      }
                    />
                    <YAxis yAxisId="equity" />
                    <YAxis yAxisId="drawdown" orientation="right" />
                    <Tooltip
                      formatter={(value: number, name: string) => [
                        name === "equity"
                          ? formatCurrency(value)
                          : formatPercent(value),
                        name === "equity" ? "Equity" : "Drawdown",
                      ]}
                      labelFormatter={(label) => formatDate(label as string)}
                    />
                    <Line
                      yAxisId="equity"
                      type="monotone"
                      dataKey="equity"
                      stroke="#2563eb"
                      dot={false}
                      name="Equity"
                    />
                    <Line
                      yAxisId="drawdown"
                      type="monotone"
                      dataKey="drawdown"
                      stroke="#dc2626"
                      dot={false}
                      name="Drawdown"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent className="" value="monthly">
          <Card className="">
            <CardHeader className="">
              <CardTitle className="">Monthly Returns</CardTitle>
            </CardHeader>
            <CardContent className="">
              <div className="h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={results.monthlyReturns}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis tickFormatter={(value) => `${value}%`} />
                    <Tooltip
                      formatter={(value: number) => [
                        `${value.toFixed(2)}%`,
                        "Return",
                      ]}
                    />
                    <Bar
                      dataKey="return"
                      fill="#2563eb"
                      name="Monthly Return"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent className="" value="trades">
          <Card className="">
            <CardHeader className="">
              <CardTitle className="">Trade History</CardTitle>
            </CardHeader>
            <CardContent className="">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr>
                      <th className="text-left p-2">Time</th>
                      <th className="text-left p-2">Type</th>
                      <th className="text-right p-2">Entry Price</th>
                      <th className="text-right p-2">Exit Price</th>
                      <th className="text-right p-2">Size</th>
                      <th className="text-right p-2">P&L</th>
                      <th className="text-right p-2">Return</th>
                      <th className="text-right p-2">Duration</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.trades.map((trade, index) => (
                      <tr key={index} className="border-t">
                        <td className="p-2">{formatDate(trade.timestamp)}</td>
                        <td
                          className={`p-2 ${trade.type === "buy" ? "text-green-500" : "text-red-500"}`}
                        >
                          {trade.type.toUpperCase()}
                        </td>
                        <td className="text-right p-2">
                          {formatCurrency(trade.entryPrice)}
                        </td>
                        <td className="text-right p-2">
                          {formatCurrency(trade.exitPrice)}
                        </td>
                        <td className="text-right p-2">
                          {trade.size.toFixed(8)}
                        </td>
                        <td
                          className={`text-right p-2 ${trade.pnl >= 0 ? "text-green-500" : "text-red-500"}`}
                        >
                          {formatCurrency(trade.pnl)}
                        </td>
                        <td
                          className={`text-right p-2 ${trade.returnPercent >= 0 ? "text-green-500" : "text-red-500"}`}
                        >
                          {formatPercent(trade.returnPercent)}
                        </td>
                        <td className="text-right p-2">{`${trade.duration}m`}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent className="" value="metrics">
          <Card className="">
            <CardHeader className="">
              <CardTitle className="">Performance Metrics</CardTitle>
            </CardHeader>
            <CardContent className="">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries({
                  "Total Return": formatPercent(metrics.totalReturn),
                  "Annualized Return": formatPercent(metrics.annualizedReturn),
                  "Sharpe Ratio": metrics.sharpeRatio.toFixed(2),
                  "Sortino Ratio": metrics.sortinoRatio.toFixed(2),
                  "Max Drawdown": formatPercent(metrics.maxDrawdown),
                  "Win Rate": formatPercent(metrics.winRate),
                  "Profit Factor": metrics.profitFactor.toFixed(2),
                  "Total Trades": metrics.totalTrades,
                  "Average Trade Return": formatPercent(
                    metrics.averageTradeReturn,
                  ),
                  "Average Winning Trade": formatCurrency(
                    metrics.averageWinningTrade,
                  ),
                  "Average Losing Trade": formatCurrency(
                    metrics.averageLosingTrade,
                  ),
                  "Average Duration": `${metrics.averageDuration}m`,
                }).map(([label, value]) => (
                  <div key={label} className="space-y-2">
                    <p className="text-sm text-gray-500">{label}</p>
                    <p className="text-lg font-medium">{value}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ResultsView;
