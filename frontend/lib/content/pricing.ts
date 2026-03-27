import type { ComponentProps } from "react"
import type { Button } from "@/components/ui/button"

type ButtonVariant = NonNullable<ComponentProps<typeof Button>["variant"]>

export type PlanId = "standard"

export type PricingFeature = Readonly<{
  label: string
  included: boolean
}>

export type PricingPlan = Readonly<{
  id: PlanId
  name: string
  description: string
  monthly: number
  cta: string
  ctaVariant: ButtonVariant
  features: ReadonlyArray<PricingFeature>
}>

export type PricingFaq = Readonly<{
  question: string
  answer: string
}>

export const PRICING_PLANS = [
  {
    id: "standard",
    name: "Standard",
    description: "For county and regional teams publishing weekly reports.",
    monthly: 10,
    cta: "Get Started",
    ctaVariant: "default",
    features: [
      { label: "Weekly PDF reports", included: true },
      { label: "Ward-level breakdowns", included: true },
      { label: "Automation scheduler", included: true },
      { label: "Email distribution", included: true },
      { label: "Audit logs", included: true },
    ],
  },
] as const satisfies ReadonlyArray<PricingPlan>

export const PRICING_FAQS = [
  {
    question: "Can I upgrade or downgrade later?",
    answer:
      "Yes. You can switch plans anytime, and changes take effect on the next billing cycle.",
  },
  {
    question: "What happens if we hit usage limits?",
    answer:
      "We'll notify you when you're approaching limits. You can upgrade, or we'll pause additional report generation until the next cycle.",
  },
  {
    question: "Can I cancel at any time?",
    answer:
      "Absolutely. Cancel whenever you need - your plan stays active until the end of the current billing period.",
  },
  {
    question: "Do you offer annual billing discounts?",
    answer:
      "Annual billing is available if your organization prefers a single payment cycle.",
  },
] as const satisfies ReadonlyArray<PricingFaq>
