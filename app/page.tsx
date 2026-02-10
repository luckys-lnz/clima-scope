"use client"

import Link from "next/link"
import { Cloud, TrendingUp, BarChart3, MapPin, Lock, Zap } from "lucide-react"


export default function Home() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Navigation */}
      <nav className="border-b border-border/40 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cloud className="w-8 h-8 text-accent-blue" />
            <span className="text-xl font-bold">cimate scoop</span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/sign-in"
              className="px-4 py-2 text-sm font-medium rounded-lg hover:bg-secondary transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/sign-up"
              className="px-4 py-2 text-sm font-medium bg-accent-blue text-white rounded-lg hover:bg-accent-blue/90 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 text-center">
        <div className="space-y-6 mb-12">
          <h1 className="text-5xl md:text-6xl font-bold text-balance">
            Automated Weekly County <span className="text-accent-blue">Weather</span> Reporting
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto text-balance">
            Real-time forecasting and reporting for all 47 Kenyan counties. Generate comprehensive weather reports with
            integrated geospatial data and automated distribution.
          </p>
          <div className="flex col sm:row gap-4 justify-center pt-4">
            <Link
              href="/sign-up"
              className="px-8 py-3 bg-accent-blue text-white rounded-lg font-medium hover:bg-accent-blue/90 transition-colors"
            >
              Start Reporting
            </Link>
            <Link
              href="/sign-in"
              className="px-8 py-3 border border-border rounded-lg font-medium hover:bg-secondary transition-colors"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-secondary/30 py-20 border-y border-border/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-16">Powerful Features</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-6 rounded-lg border border-border/40 hover:border-border/80 transition-colors bg-card">
              <BarChart3 className="w-12 h-12 text-accent-blue mb-4" />
              <h3 className="text-lg font-semibold mb-2">Automated Generation</h3>
              <p className="text-sm text-muted-foreground">
                Generate comprehensive weather reports with a single click. Process GRIB data and integrate real-time
                observations automatically.
              </p>
            </div>
            <div className="p-6 rounded-lg border border-border/40 hover:border-border/80 transition-colors bg-card">
              <MapPin className="w-12 h-12 text-accent-orange mb-4" />
              <h3 className="text-lg font-semibold mb-2">Geospatial Data</h3>
              <p className="text-sm text-muted-foreground">
                Visualize county-level and ward-level data on interactive maps. Overlay multiple data layers for
                comprehensive analysis.
              </p>
            </div>
            <div className="p-6 rounded-lg border border-border/40 hover:border-border/80 transition-colors bg-card">
              <TrendingUp className="w-12 h-12 text-accent-green mb-4" />
              <h3 className="text-lg font-semibold mb-2">Real-time Monitoring</h3>
              <p className="text-sm text-muted-foreground">
                Monitor system health, pipeline status, and processing logs. Get instant alerts for anomalies and
                errors.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Capabilities Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-16">Everything You Need</h2>
          <div className="grid sm:grid-cols-2 gap-12">
            <div className="space-y-6">
              <div className="flex gap-4">
                <Zap className="w-6 h-6 text-accent-blue shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold mb-2">Manual Report Generation</h3>
                  <p className="text-sm text-muted-foreground">
                    Create custom reports on demand with full control over parameters and scheduling.
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <BarChart3 className="w-6 h-6 text-accent-orange shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold mb-2">Report Archive</h3>
                  <p className="text-sm text-muted-foreground">
                    Access all generated reports with advanced filtering and historical analysis.
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <Lock className="w-6 h-6 text-accent-green shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold mb-2">System Configuration</h3>
                  <p className="text-sm text-muted-foreground">
                    Configure GRIB storage, email distribution, and automated scheduling.
                  </p>
                </div>
              </div>
            </div>
            <div className="space-y-6">
              <div className="flex gap-4">
                <Cloud className="w-6 h-6 text-accent-blue shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold mb-2">Data Management</h3>
                  <p className="text-sm text-muted-foreground">
                    Upload and verify shapefiles, observations, and configuration data with validation checks.
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <TrendingUp className="w-6 h-6 text-accent-orange shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold mb-2">Comprehensive Logging</h3>
                  <p className="text-sm text-muted-foreground">
                    Track all system activity with detailed logs and diagnostics for troubleshooting.
                  </p>
                </div>
              </div>
              <div className="flex gap-4">
                <MapPin className="w-6 h-6 text-accent-green shrink-0 mt-1" />
                <div>
                  <h3 className="font-semibold mb-2">County Details</h3>
                  <p className="text-sm text-muted-foreground">
                    View detailed forecasts with ward-level breakdown and geospatial visualizations.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-secondary/50 border-y border-border/40 py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          <h2 className="text-3xl font-bold">Ready to get started?</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Join Kenya's automated weather reporting system. Generate, analyze, and distribute forecasts to all 47
            counties in minutes.
          </p>
          <Link
            href="/sign-up"
            className="inline-block px-8 py-3 bg-accent-blue text-white rounded-lg font-medium hover:bg-accent-blue/90 transition-colors"
          >
            Create Your Account
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/40 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-muted-foreground">
          <p>&copy; 2026 Kenya Meteorological Institute. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
