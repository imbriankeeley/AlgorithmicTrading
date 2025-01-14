import React from "react";
import { Activity, LineChart, History, Settings } from "lucide-react";

const RootLayout = ({ children }) => {
  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar Navigation */}
      <div className="w-64 border-r bg-card">
        <div className="p-6">
          <h1 className="text-xl font-bold">Crypto Trading Bot</h1>
        </div>
        <nav className="space-y-2 px-4">
          <a
            href="/dashboard"
            className="flex items-center space-x-2 p-2 rounded-lg hover:bg-accent text-foreground/60 hover:text-foreground"
          >
            <Activity className="h-5 w-5" />
            <span>Dashboard</span>
          </a>
          <a
            href="/trading"
            className="flex items-center space-x-2 p-2 rounded-lg hover:bg-accent text-foreground/60 hover:text-foreground"
          >
            <LineChart className="h-5 w-5" />
            <span>Trading</span>
          </a>
          <a
            href="/history"
            className="flex items-center space-x-2 p-2 rounded-lg hover:bg-accent text-foreground/60 hover:text-foreground"
          >
            <History className="h-5 w-5" />
            <span>History</span>
          </a>
          <a
            href="/settings"
            className="flex items-center space-x-2 p-2 rounded-lg hover:bg-accent text-foreground/60 hover:text-foreground"
          >
            <Settings className="h-5 w-5" />
            <span>Settings</span>
          </a>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        <header className="border-b">
          <div className="h-16 flex items-center px-6">
            <h2 className="text-lg font-semibold">Trading Dashboard</h2>
          </div>
        </header>
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
};

export default RootLayout;
