import Link from "next/link"
import { ArrowLeft } from "lucide-react"

import { PricingSection } from "@/components/marketing/pricing-section"

export default function PricingPage() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto w-full max-w-6xl px-6 pt-6">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Link>
      </div>
      <PricingSection headingLevel="h1" />
    </main>
  )
}
