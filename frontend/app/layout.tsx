import type React from "react";
import type { Metadata, Viewport } from "next";
import { Analytics } from "@vercel/analytics/next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Weather Reporting System - Kenya County Forecasts",
  description:
    "Automated weekly county-level weather reporting using GFS 7-day forecast data",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        suppressHydrationWarning
        className={`font-sans antialiased overflow-x-hidden`}
      >
        {children}
        <Analytics />
      </body>
    </html>
  );
}
