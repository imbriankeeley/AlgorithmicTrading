"use client";
import React from "react";
import TradingView from "@/components/trading/TradingView";
import PerformanceMetrics from "@/components/dashboard/PerformanceMetrics";

export const DashboardPage = () => {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TradingView />
        <PerformanceMetrics />
      </div>
    </div>
  );
};
