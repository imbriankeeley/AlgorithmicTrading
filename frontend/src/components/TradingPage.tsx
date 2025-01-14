import React, { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Alert,
  AlertDescription,
} from "./ui-components";
import { AlertCircle } from "lucide-react";
import TradingView from "./trading/TradingView";
import OrderForm from "./trading/OrderForm";

export const TradingPage = () => {
  const [showOrderForm, setShowOrderForm] = useState(false);
  const [orderType, setOrderType] = useState<"buy" | "sell">("buy");
  const [error, setError] = useState<string | null>(null);

  const handlePlaceOrder = async (orderData: any) => {
    try {
      const response = await fetch("/api/trading/orders", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(orderData),
      });

      if (!response.ok) {
        throw new Error("Failed to place order");
      }

      setShowOrderForm(false);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to place order");
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

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Trading View */}
        <div className="lg:col-span-2">
          <Card className="">
            <CardHeader className="">
              <CardTitle className="">BTC/USD</CardTitle>
            </CardHeader>
            <CardContent className="">
              <TradingView />
            </CardContent>
          </Card>
        </div>

        {/* Order Form or Trading Controls */}
        <div className="lg:col-span-1">
          {showOrderForm ? (
            <OrderForm
              symbol="BTC-USD"
              defaultSize={0.01}
              onSubmit={handlePlaceOrder}
              onClose={() => setShowOrderForm(false)}
            />
          ) : (
            <Card className="">
              <CardHeader className="">
                <CardTitle className="">Trading Controls</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  className="w-full"
                  onClick={() => {
                    setOrderType("buy");
                    setShowOrderForm(true);
                  }}
                >
                  Place Buy Order
                </Button>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    setOrderType("sell");
                    setShowOrderForm(true);
                  }}
                >
                  Place Sell Order
                </Button>
                <Button
                  variant="destructive"
                  className="w-full"
                  onClick={async () => {
                    try {
                      await fetch("/api/trading/emergency/stop", {
                        method: "POST",
                      });
                    } catch (err) {
                      setError("Failed to execute emergency stop");
                    }
                  }}
                >
                  Emergency Stop
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
