import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Input,
  Alert,
  AlertDescription,
} from "@/components/ui-components";
import { AlertCircle, ArrowUp, ArrowDown } from "lucide-react";

interface OrderFormProps {
  symbol?: string;
  defaultSize?: number;
  onSubmit?: (order: OrderData) => Promise<void>;
  onClose?: () => void;
}

interface OrderData {
  symbol: string;
  type: "buy" | "sell";
  size: number;
  takeProfit: number;
  stopLoss: number;
}

const OrderForm: React.FC<OrderFormProps> = ({
  symbol = "BTC-USD",
  defaultSize = 0.01,
  onSubmit,
  onClose,
}) => {
  // Form state
  const [orderType, setOrderType] = useState<"buy" | "sell">("buy");
  const [size, setSize] = useState<string>(defaultSize.toString());
  const [takeProfit, setTakeProfit] = useState<string>("");
  const [stopLoss, setStopLoss] = useState<string>("");
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orderPreview, setOrderPreview] = useState<{
    total: number;
    fees: number;
  } | null>(null);

  // Fetch current price and setup WebSocket connection
  useEffect(() => {
    const fetchPrice = async () => {
      try {
        const response = await fetch(`/api/trading/prices/${symbol}/current`);
        const data = await response.json();
        setCurrentPrice(data.price);
      } catch (err) {
        setError("Failed to fetch current price");
      }
    };

    fetchPrice();
    const interval = setInterval(fetchPrice, 5000);

    // WebSocket for real-time price updates
    const ws = new WebSocket(`ws://localhost:8000/ws/prices/${symbol}`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setCurrentPrice(data.price);
    };

    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, [symbol]);

  // Calculate order preview when inputs change
  useEffect(() => {
    if (currentPrice && size) {
      const sizeNum = parseFloat(size);
      const total = currentPrice * sizeNum;
      const fees = total * 0.001; // 0.1% fee
      setOrderPreview({ total, fees });
    } else {
      setOrderPreview(null);
    }
  }, [currentPrice, size]);

  // Validate form inputs
  const validateInputs = (): boolean => {
    if (!currentPrice) {
      setError("Current price not available");
      return false;
    }

    const sizeNum = parseFloat(size);
    const takeProfitNum = parseFloat(takeProfit);
    const stopLossNum = parseFloat(stopLoss);

    if (isNaN(sizeNum) || sizeNum <= 0) {
      setError("Invalid position size");
      return false;
    }

    if (isNaN(takeProfitNum) || isNaN(stopLossNum)) {
      setError("Invalid take profit or stop loss");
      return false;
    }

    if (orderType === "buy") {
      if (takeProfitNum <= currentPrice) {
        setError(
          "Take profit must be higher than current price for buy orders",
        );
        return false;
      }
      if (stopLossNum >= currentPrice) {
        setError("Stop loss must be lower than current price for buy orders");
        return false;
      }
    } else {
      if (takeProfitNum >= currentPrice) {
        setError(
          "Take profit must be lower than current price for sell orders",
        );
        return false;
      }
      if (stopLossNum <= currentPrice) {
        setError("Stop loss must be higher than current price for sell orders");
        return false;
      }
    }

    return true;
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateInputs()) {
      return;
    }

    setLoading(true);
    try {
      const orderData: OrderData = {
        symbol,
        type: orderType,
        size: parseFloat(size),
        takeProfit: parseFloat(takeProfit),
        stopLoss: parseFloat(stopLoss),
      };

      await onSubmit?.(orderData);
      onClose?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to place order");
    } finally {
      setLoading(false);
    }
  };

  // Format currency values
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
    }).format(value);
  };

  return (
    <Card className="w-full max-w-lg">
      <CardHeader className="">
        <CardTitle className="flex items-center justify-between">
          <span>Place {orderType === "buy" ? "Buy" : "Sell"} Order</span>
          {currentPrice && (
            <span className="text-lg">{formatCurrency(currentPrice)}</span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Order Type Toggle */}
          <div className="grid grid-cols-2 gap-4">
            <Button
              type="button"
              variant={orderType === "buy" ? "default" : "outline"}
              className="w-full"
              onClick={() => setOrderType("buy")}
            >
              <ArrowUp className="mr-2 h-4 w-4" />
              Buy
            </Button>
            <Button
              type="button"
              variant={orderType === "sell" ? "default" : "outline"}
              className="w-full"
              onClick={() => setOrderType("sell")}
            >
              <ArrowDown className="mr-2 h-4 w-4" />
              Sell
            </Button>
          </div>

          {/* Position Size Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Position Size ({symbol.split("-")[0]})
            </label>
            <Input
              type="number"
              value={size}
              onChange={(e) => setSize(e.target.value)}
              step="0.00001"
              min="0.00001"
              required
            />
          </div>

          {/* Take Profit Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Take Profit (USD)</label>
            <Input
              type="number"
              value={takeProfit}
              onChange={(e) => setTakeProfit(e.target.value)}
              step="0.01"
              required
            />
          </div>

          {/* Stop Loss Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Stop Loss (USD)</label>
            <Input
              type="number"
              value={stopLoss}
              onChange={(e) => setStopLoss(e.target.value)}
              step="0.01"
              required
            />
          </div>

          {/* Order Preview */}
          {orderPreview && (
            <div className="p-4 bg-gray-50 rounded-md space-y-2">
              <div className="flex justify-between">
                <span>Total Value:</span>
                <span>{formatCurrency(orderPreview.total)}</span>
              </div>
              <div className="flex justify-between text-sm text-gray-500">
                <span>Estimated Fees:</span>
                <span>{formatCurrency(orderPreview.fees)}</span>
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <Alert className="" variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="">{error}</AlertDescription>
            </Alert>
          )}

          {/* Submit Button */}
          <div className="flex space-x-4">
            <Button
              type="submit"
              className="w-full"
              disabled={loading || !currentPrice}
            >
              {loading ? "Placing Order..." : "Place Order"}
            </Button>
            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={onClose}
            >
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default OrderForm;
