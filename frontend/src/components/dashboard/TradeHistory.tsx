import React, { useState, useCallback } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Input,
  Button,
  Alert,
  AlertDescription,
} from "@/components/ui-components";
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
  Download,
  Search,
  AlertCircle,
  ArrowUp,
  ArrowDown,
  RefreshCcw,
} from "lucide-react";

interface Trade {
  id: string;
  timestamp: string;
  symbol: string;
  type: "buy" | "sell";
  entryPrice: number;
  exitPrice: number;
  size: number;
  pnl: number;
  status: "open" | "closed";
  strategy: string;
}

interface TradeHistoryProps {
  initialTrades?: Trade[];
  onRefresh?: () => void;
}

const TradeHistory: React.FC<TradeHistoryProps> = ({
  initialTrades = [],
  onRefresh,
}) => {
  const [trades, setTrades] = useState<Trade[]>(initialTrades);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState<keyof Trade>("timestamp");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

  // Format currency values
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Format dates
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  // Filter trades based on search term
  const filteredTrades = trades.filter(
    (trade) =>
      trade.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      trade.strategy.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  // Sort trades
  const sortedTrades = [...filteredTrades].sort((a, b) => {
    const aValue = a[sortField];
    const bValue = b[sortField];

    if (typeof aValue === "string" && typeof bValue === "string") {
      return sortDirection === "asc"
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    }

    if (typeof aValue === "number" && typeof bValue === "number") {
      return sortDirection === "asc" ? aValue - bValue : bValue - aValue;
    }

    return 0;
  });

  // Calculate cumulative PnL for chart
  const cumulativePnL = sortedTrades.reduce(
    (acc, trade) => {
      if (trade.status === "closed") {
        const lastValue = acc.length > 0 ? acc[acc.length - 1].value : 0;
        acc.push({
          timestamp: trade.timestamp,
          value: lastValue + trade.pnl,
        });
      }
      return acc;
    },
    [] as Array<{ timestamp: string; value: number }>,
  );

  // Export trades to CSV
  const exportToCsv = useCallback(() => {
    const headers = [
      "Date",
      "Symbol",
      "Type",
      "Entry Price",
      "Exit Price",
      "Size",
      "PnL",
      "Status",
      "Strategy",
    ];
    const csvContent = [
      headers.join(","),
      ...sortedTrades.map((trade) =>
        [
          formatDate(trade.timestamp),
          trade.symbol,
          trade.type,
          trade.entryPrice,
          trade.exitPrice,
          trade.size,
          trade.pnl,
          trade.status,
          trade.strategy,
        ].join(","),
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute(
      "download",
      `trade_history_${new Date().toISOString()}.csv`,
    );
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [sortedTrades]);

  return (
    <div className="space-y-6">
      {/* Error Alert */}
      {error && (
        <Alert className="" variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="">{error}</AlertDescription>
        </Alert>
      )}

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
        <div className="flex gap-2 w-full sm:w-auto">
          <Input
            placeholder="Search trades..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="max-w-sm"
          />
          <Button
            className=""
            variant="outline"
            onClick={onRefresh}
            disabled={loading}
          >
            <RefreshCcw
              className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
            />
          </Button>
        </div>
        <Button
          className=""
          variant="outline"
          onClick={exportToCsv}
          disabled={sortedTrades.length === 0}
        >
          <Download className="h-4 w-4 mr-2" />
          Export CSV
        </Button>
      </div>

      {/* PnL Chart */}
      <Card className="">
        <CardHeader className="">
          <CardTitle className="">Cumulative P&L</CardTitle>
        </CardHeader>
        <CardContent className="">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={cumulativePnL}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(value) =>
                    new Date(value).toLocaleDateString()
                  }
                />
                <YAxis tickFormatter={(value) => formatCurrency(value)} />
                <Tooltip
                  formatter={(value: number) => [formatCurrency(value), "P&L"]}
                  labelFormatter={(label) =>
                    new Date(label as string).toLocaleString()
                  }
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#2563eb"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Trade Table */}
      <Card className="">
        <CardHeader className="">
          <CardTitle className="">Trade History</CardTitle>
        </CardHeader>
        <CardContent className="">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="text-left p-2">Date</th>
                  <th className="text-left p-2">Symbol</th>
                  <th className="text-left p-2">Type</th>
                  <th className="text-right p-2">Entry Price</th>
                  <th className="text-right p-2">Exit Price</th>
                  <th className="text-right p-2">Size</th>
                  <th className="text-right p-2">P&L</th>
                  <th className="text-right p-2">Status</th>
                  <th className="text-right p-2">Strategy</th>
                </tr>
              </thead>
              <tbody>
                {sortedTrades.map((trade) => (
                  <tr key={trade.id} className="border-t hover:bg-gray-50">
                    <td className="p-2">{formatDate(trade.timestamp)}</td>
                    <td className="p-2">{trade.symbol}</td>
                    <td className="p-2">
                      <span className="flex items-center">
                        {trade.type === "buy" ? (
                          <ArrowUp className="h-4 w-4 text-green-500 mr-1" />
                        ) : (
                          <ArrowDown className="h-4 w-4 text-red-500 mr-1" />
                        )}
                        {trade.type.toUpperCase()}
                      </span>
                    </td>
                    <td className="text-right p-2">
                      {formatCurrency(trade.entryPrice)}
                    </td>
                    <td className="text-right p-2">
                      {trade.exitPrice ? formatCurrency(trade.exitPrice) : "-"}
                    </td>
                    <td className="text-right p-2">{trade.size.toFixed(8)}</td>
                    <td
                      className={`text-right p-2 ${
                        trade.pnl >= 0 ? "text-green-500" : "text-red-500"
                      }`}
                    >
                      {formatCurrency(trade.pnl)}
                    </td>
                    <td className="text-right p-2">
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                          trade.status === "open"
                            ? "bg-blue-100 text-blue-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {trade.status.toUpperCase()}
                      </span>
                    </td>
                    <td className="text-right p-2">{trade.strategy}</td>
                  </tr>
                ))}
                {sortedTrades.length === 0 && (
                  <tr>
                    <td colSpan={9} className="text-center py-8 text-gray-500">
                      No trades found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TradeHistory;
