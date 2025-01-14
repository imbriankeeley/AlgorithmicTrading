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
} from "./ui-components";
import { AlertCircle, Save } from "lucide-react";

interface StrategySettings {
  shortEmaPeriod: number;
  longEmaPeriod: number;
  takeProfitPct: number;
  stopLossPct: number;
  positionSizePct: number;
}

interface RiskSettings {
  maxPositionSize: number;
  maxDailyDrawdown: number;
  maxTradesPerDay: number;
  emergencyStopLoss: number;
}

interface NotificationSettings {
  enableSmsAlerts: boolean;
  phoneNumber: string;
  alertOnTrades: boolean;
  alertOnErrors: boolean;
}

export const SettingsPage = () => {
  const [strategySettings, setStrategySettings] = useState<StrategySettings>({
    shortEmaPeriod: 9,
    longEmaPeriod: 21,
    takeProfitPct: 2.0,
    stopLossPct: 1.0,
    positionSizePct: 1.0,
  });

  const [riskSettings, setRiskSettings] = useState<RiskSettings>({
    maxPositionSize: 1000,
    maxDailyDrawdown: 5.0,
    maxTradesPerDay: 10,
    emergencyStopLoss: 15.0,
  });

  const [notificationSettings, setNotificationSettings] =
    useState<NotificationSettings>({
      enableSmsAlerts: false,
      phoneNumber: "",
      alertOnTrades: true,
      alertOnErrors: true,
    });

  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch("/api/trading/settings");
      if (!response.ok) throw new Error("Failed to fetch settings");
      const data = await response.json();

      setStrategySettings(data.strategy);
      setRiskSettings(data.risk);
      setNotificationSettings(data.notifications);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch settings");
    }
  };

  const handleSaveSettings = async () => {
    try {
      setIsSaving(true);
      setError(null);
      setSuccessMessage(null);

      const response = await fetch("/api/trading/settings", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          strategy: strategySettings,
          risk: riskSettings,
          notifications: notificationSettings,
        }),
      });

      if (!response.ok) throw new Error("Failed to save settings");

      setSuccessMessage("Settings saved successfully");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setIsSaving(false);
    }
  };

  const validatePhoneNumber = (number: string) => {
    // Basic phone number validation
    const phoneRegex = /^\+?[\d\s-]{10,}$/;
    return phoneRegex.test(number);
  };

  return (
    <div className="space-y-6">
      {error && (
        <Alert className="" variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="">{error}</AlertDescription>
        </Alert>
      )}

      {successMessage && (
        <Alert variant="default" className="">
          <AlertDescription className="">{successMessage}</AlertDescription>
        </Alert>
      )}

      {/* Strategy Settings */}
      <Card className="">
        <CardHeader className="">
          <CardTitle className="">Strategy Settings</CardTitle>
        </CardHeader>
        <CardContent className="">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Short EMA Period</label>
              <Input
                type="number"
                value={strategySettings.shortEmaPeriod}
                onChange={(e) =>
                  setStrategySettings({
                    ...strategySettings,
                    shortEmaPeriod: parseInt(e.target.value),
                  })
                }
                min={1}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Long EMA Period</label>
              <Input
                type="number"
                value={strategySettings.longEmaPeriod}
                onChange={(e) =>
                  setStrategySettings({
                    ...strategySettings,
                    longEmaPeriod: parseInt(e.target.value),
                  })
                }
                min={1}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Take Profit (%)</label>
              <Input
                type="number"
                step="0.1"
                value={strategySettings.takeProfitPct}
                onChange={(e) =>
                  setStrategySettings({
                    ...strategySettings,
                    takeProfitPct: parseFloat(e.target.value),
                  })
                }
                min={0.1}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Stop Loss (%)</label>
              <Input
                type="number"
                step="0.1"
                value={strategySettings.stopLossPct}
                onChange={(e) =>
                  setStrategySettings({
                    ...strategySettings,
                    stopLossPct: parseFloat(e.target.value),
                  })
                }
                min={0.1}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Position Size (%)</label>
              <Input
                type="number"
                step="0.1"
                value={strategySettings.positionSizePct}
                onChange={(e) =>
                  setStrategySettings({
                    ...strategySettings,
                    positionSizePct: parseFloat(e.target.value),
                  })
                }
                min={0.1}
                max={100}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risk Management Settings */}
      <Card className="">
        <CardHeader className="">
          <CardTitle className="">Risk Management</CardTitle>
        </CardHeader>
        <CardContent className="">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Max Position Size (USD)
              </label>
              <Input
                type="number"
                value={riskSettings.maxPositionSize}
                onChange={(e) =>
                  setRiskSettings({
                    ...riskSettings,
                    maxPositionSize: parseInt(e.target.value),
                  })
                }
                min={0}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Max Daily Drawdown (%)
              </label>
              <Input
                type="number"
                step="0.1"
                value={riskSettings.maxDailyDrawdown}
                onChange={(e) =>
                  setRiskSettings({
                    ...riskSettings,
                    maxDailyDrawdown: parseFloat(e.target.value),
                  })
                }
                min={0}
                max={100}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Max Trades Per Day</label>
              <Input
                type="number"
                value={riskSettings.maxTradesPerDay}
                onChange={(e) =>
                  setRiskSettings({
                    ...riskSettings,
                    maxTradesPerDay: parseInt(e.target.value),
                  })
                }
                min={1}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Emergency Stop Loss (%)
              </label>
              <Input
                type="number"
                step="0.1"
                value={riskSettings.emergencyStopLoss}
                onChange={(e) =>
                  setRiskSettings({
                    ...riskSettings,
                    emergencyStopLoss: parseFloat(e.target.value),
                  })
                }
                min={0}
                max={100}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notification Settings */}
      <Card className="">
        <CardHeader className="">
          <CardTitle className="">Notifications</CardTitle>
        </CardHeader>
        <CardContent className="">
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="enableSmsAlerts"
                checked={notificationSettings.enableSmsAlerts}
                onChange={(e) =>
                  setNotificationSettings({
                    ...notificationSettings,
                    enableSmsAlerts: e.target.checked,
                  })
                }
                className="h-4 w-4 rounded border-gray-300"
              />
              <label htmlFor="enableSmsAlerts" className="text-sm font-medium">
                Enable SMS Alerts
              </label>
            </div>

            {notificationSettings.enableSmsAlerts && (
              <div className="space-y-2">
                <label className="text-sm font-medium">Phone Number</label>
                <Input
                  type="tel"
                  value={notificationSettings.phoneNumber}
                  onChange={(e) =>
                    setNotificationSettings({
                      ...notificationSettings,
                      phoneNumber: e.target.value,
                    })
                  }
                  placeholder="+1234567890"
                />
                {notificationSettings.phoneNumber &&
                  !validatePhoneNumber(notificationSettings.phoneNumber) && (
                    <p className="text-sm text-red-500">
                      Please enter a valid phone number
                    </p>
                  )}
              </div>
            )}

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="alertOnTrades"
                checked={notificationSettings.alertOnTrades}
                onChange={(e) =>
                  setNotificationSettings({
                    ...notificationSettings,
                    alertOnTrades: e.target.checked,
                  })
                }
                className="h-4 w-4 rounded border-gray-300"
              />
              <label htmlFor="alertOnTrades" className="text-sm font-medium">
                Alert on Trades
              </label>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="alertOnErrors"
                checked={notificationSettings.alertOnErrors}
                onChange={(e) =>
                  setNotificationSettings({
                    ...notificationSettings,
                    alertOnErrors: e.target.checked,
                  })
                }
                className="h-4 w-4 rounded border-gray-300"
              />
              <label htmlFor="alertOnErrors" className="text-sm font-medium">
                Alert on Errors
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSaveSettings}
          disabled={
            isSaving ||
            (notificationSettings.enableSmsAlerts &&
              !validatePhoneNumber(notificationSettings.phoneNumber))
          }
          className="flex items-center space-x-2"
        >
          <Save className="h-4 w-4" />
          <span>{isSaving ? "Saving..." : "Save Settings"}</span>
        </Button>
      </div>
    </div>
  );
};
