import React, { useState } from "react";
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
import { Upload, Calendar, AlertCircle } from "lucide-react";
import Papa from "papaparse";

interface BacktestFormProps {
  onSubmit: (config: BacktestConfig) => Promise<void>;
  isSubmitting?: boolean;
}

interface BacktestConfig {
  strategyParams: {
    shortEmaPeriod: number;
    longEmaPeriod: number;
    takeProfitPct: number;
    stopLossPct: number;
    positionSizePct: number;
  };
  backtestParams: {
    initialCapital: number;
    tradingFees: number;
    includeFees: boolean;
    includeSlippage: boolean;
    startDate: string;
    endDate: string;
  };
  historicalData: string | null;
}

const BacktestForm: React.FC<BacktestFormProps> = ({
  onSubmit,
  isSubmitting = false,
}) => {
  const [config, setConfig] = useState<BacktestConfig>({
    strategyParams: {
      shortEmaPeriod: 9,
      longEmaPeriod: 21,
      takeProfitPct: 2.0,
      stopLossPct: 1.0,
      positionSizePct: 1.0,
    },
    backtestParams: {
      initialCapital: 10000,
      tradingFees: 0.1,
      includeFees: true,
      includeSlippage: true,
      startDate: "",
      endDate: "",
    },
    historicalData: null,
  });

  const [error, setError] = useState<string | null>(null);
  const [fileInfo, setFileInfo] = useState<string | null>(null);

  const handleStrategyChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type } = e.target;
    setConfig((prev) => ({
      ...prev,
      strategyParams: {
        ...prev.strategyParams,
        [name]: type === "number" ? parseFloat(value) : value,
      },
    }));
  };

  const handleBacktestChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setConfig((prev) => ({
      ...prev,
      backtestParams: {
        ...prev.backtestParams,
        [name]:
          type === "checkbox"
            ? checked
            : type === "number"
              ? parseFloat(value)
              : value,
      },
    }));
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith(".csv")) {
      setError("Please upload a CSV file");
      return;
    }

    try {
      const csvData = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target?.result as string);
        reader.onerror = (e) => reject(e);
        reader.readAsText(file);
      });

      Papa.parse(csvData, {
        header: true,
        error: (error) => {
          setError(`Invalid CSV format: ${error}`);
        },
        complete: (results) => {
          const requiredColumns = [
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
          ];
          const headers = Object.keys(results.data[0] || {});

          const missingColumns = requiredColumns.filter(
            (col) => !headers.includes(col),
          );

          if (missingColumns.length > 0) {
            setError(`Missing required columns: ${missingColumns.join(", ")}`);
            return;
          }

          setConfig((prev) => ({ ...prev, historicalData: csvData }));
          setFileInfo(
            `Loaded ${results.data.length} data points from ${file.name}`,
          );
          setError(null);
        },
      });
    } catch (err) {
      setError("Failed to read file");
    }
  };

  const validateForm = (): boolean => {
    if (!config.historicalData) {
      setError("Please upload historical data");
      return false;
    }

    if (!config.backtestParams.startDate || !config.backtestParams.endDate) {
      setError("Please select date range");
      return false;
    }

    if (
      new Date(config.backtestParams.startDate) >=
      new Date(config.backtestParams.endDate)
    ) {
      setError("End date must be after start date");
      return false;
    }

    if (
      config.strategyParams.stopLossPct >= config.strategyParams.takeProfitPct
    ) {
      setError("Take profit must be greater than stop loss");
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      return;
    }

    try {
      await onSubmit(config);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start backtest");
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader className="">
        <CardTitle className="">Backtest Configuration</CardTitle>
      </CardHeader>
      <CardContent className="">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Strategy Parameters */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Strategy Parameters</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Short EMA Period</label>
                <Input
                  type="number"
                  name="shortEmaPeriod"
                  value={config.strategyParams.shortEmaPeriod}
                  onChange={handleStrategyChange}
                  min="1"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Long EMA Period</label>
                <Input
                  type="number"
                  name="longEmaPeriod"
                  value={config.strategyParams.longEmaPeriod}
                  onChange={handleStrategyChange}
                  min="1"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Take Profit (%)</label>
                <Input
                  type="number"
                  name="takeProfitPct"
                  value={config.strategyParams.takeProfitPct}
                  onChange={handleStrategyChange}
                  step="0.1"
                  min="0.1"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Stop Loss (%)</label>
                <Input
                  type="number"
                  name="stopLossPct"
                  value={config.strategyParams.stopLossPct}
                  onChange={handleStrategyChange}
                  step="0.1"
                  min="0.1"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Position Size (%)</label>
                <Input
                  type="number"
                  name="positionSizePct"
                  value={config.strategyParams.positionSizePct}
                  onChange={handleStrategyChange}
                  step="0.1"
                  min="0.1"
                  max="100"
                  required
                />
              </div>
            </div>
          </div>

          {/* Backtest Parameters */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Backtest Parameters</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">
                  Initial Capital (USD)
                </label>
                <Input
                  type="number"
                  name="initialCapital"
                  value={config.backtestParams.initialCapital}
                  onChange={handleBacktestChange}
                  min="100"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Trading Fees (%)</label>
                <Input
                  type="number"
                  name="tradingFees"
                  value={config.backtestParams.tradingFees}
                  onChange={handleBacktestChange}
                  step="0.01"
                  min="0"
                  required
                />
              </div>
              <div className="col-span-2 grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Start Date</label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
                    <Input
                      type="date"
                      name="startDate"
                      value={config.backtestParams.startDate}
                      onChange={handleBacktestChange}
                      className="pl-10"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">End Date</label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
                    <Input
                      type="date"
                      name="endDate"
                      value={config.backtestParams.endDate}
                      onChange={handleBacktestChange}
                      className="pl-10"
                      required
                    />
                  </div>
                </div>
              </div>
              <div className="col-span-2 flex space-x-4">
                <label className="flex items-center space-x-2">
                  <Input
                    type="checkbox"
                    name="includeFees"
                    checked={config.backtestParams.includeFees}
                    onChange={handleBacktestChange}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">Include Trading Fees</span>
                </label>
                <label className="flex items-center space-x-2">
                  <Input
                    type="checkbox"
                    name="includeSlippage"
                    checked={config.backtestParams.includeSlippage}
                    onChange={handleBacktestChange}
                    className="w-4 h-4"
                  />
                  <span className="text-sm">Include Slippage</span>
                </label>
              </div>
            </div>
          </div>

          {/* Historical Data Upload */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Historical Data</h3>
            <div className="space-y-2">
              <Button
                type="button"
                variant="outline"
                className="w-full h-24"
                onClick={() => document.getElementById("file-upload")?.click()}
              >
                <div className="flex flex-col items-center space-y-2">
                  <Upload className="h-6 w-6" />
                  <span>Upload CSV file</span>
                  {fileInfo && (
                    <span className="text-sm text-gray-500">{fileInfo}</span>
                  )}
                </div>
              </Button>
              <Input
                id="file-upload"
                type="file"
                accept=".csv"
                onChange={handleFileUpload}
                className="hidden"
              />
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <Alert className="" variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="">{error}</AlertDescription>
            </Alert>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full"
            disabled={isSubmitting || !config.historicalData}
          >
            {isSubmitting ? "Running Backtest..." : "Run Backtest"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export default BacktestForm;
