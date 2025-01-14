import type { Metadata } from "next";
import { Inter } from "next/font/google";
import RootLayout from "@/components/RootLayout";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Crypto Trading Bot",
  description: "Automated cryptocurrency trading system",
};

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <RootLayout>{children}</RootLayout>
      </body>
    </html>
  );
}
