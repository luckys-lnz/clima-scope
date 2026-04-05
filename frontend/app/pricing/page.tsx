import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { PricingSection } from "@/components/marketing/pricing-section";

export default function PricingPage() {
  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 pt-6">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 text-sm font-medium text-sky-600 transition-colors hover:text-sky-700"
          aria-label="Back to dashboard"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Link>
      </div>

      <PricingSection headingLevel="h1" showFaqs={false} className="py-4" />
    </main>
  );
}
