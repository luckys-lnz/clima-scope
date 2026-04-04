import Link from "next/link";

import { PricingSection } from "@/components/marketing/pricing-section";

export default function PricingPage() {
  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 pt-6">
        <Link
          href="/dashboard"
          className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          Back to Dashboard
        </Link>
      </div>

      <PricingSection headingLevel="h1" showFaqs={false} className="py-4" />
    </main>
  );
}
