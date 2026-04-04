import Link from "next/link";
import { AlertCircle, BarChart3 } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

export default function LimitsPage() {
  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <Link
          href="/dashboard"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          Back to Dashboard
        </Link>

        <div className="space-y-1">
          <h1 className="text-3xl font-bold">Usage Limits</h1>
          <p className="text-sm text-muted-foreground">
            This page is dedicated to usage and quota visibility.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Current Usage
            </CardTitle>
            <CardDescription>
              Live quota metrics will appear here once the backend usage
              endpoint is available.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="mb-2 flex items-center justify-between text-sm">
                <span>Reports generated this cycle</span>
                <span className="text-muted-foreground">N/A</span>
              </div>
              <Progress value={0} />
            </div>

            <div className="flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-700">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <p>
                Usage telemetry is not exposed by API yet. This view is now
                separated and ready for live data wiring.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
