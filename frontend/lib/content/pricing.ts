import type { ComponentProps } from "react"
import type { Button } from "@/components/ui/button"

type ButtonVariant = NonNullable<ComponentProps<typeof Button>["variant"]>

export type PlanId = "pro"

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
  isPopular: boolean
  features: ReadonlyArray<PricingFeature>
}>

export type PricingFaq = Readonly<{
  question: string
  answer: string
}>

export const PRICING_PLANS = [
  {

    id: "pro",
    name: "Weather Reporting",
    description: "One plan with flexible monthly or yearly billing.",
    monthly: 1000,
    cta: "Go Pro",
    ctaVariant: "default",
    isPopular: false,
    features: [
      { label: "All counties", included: true },
      { label: "Weekly + on-demand reports", included: true },

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
      "Yes. Yearly billing is KES 10,000 instead of KES 12,000, which is a 16.67% discount.",
  },
  {
    question: "What's included in Enterprise support?",
    answer:
      "Enterprise includes onboarding, implementation guidance, and a dedicated support channel with an SLA.",

  },
] as const satisfies ReadonlyArray<PricingFaq>
