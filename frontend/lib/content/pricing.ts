import type { ComponentProps } from "react"
import type { Button } from "@/components/ui/button"

type ButtonVariant = NonNullable<ComponentProps<typeof Button>["variant"]>

export type PlanId = "starter" | "pro" | "enterprise"

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
  isPopular?: boolean
  features: ReadonlyArray<PricingFeature>
}>

export type PricingFaq = Readonly<{
  question: string
  answer: string
}>

export const PRICING_PLANS = [
  {
    id: "starter",
    name: "Starter",
    description: "For small teams publishing weekly county summaries.",
    monthly: 49,
    cta: "Start Starter",
    ctaVariant: "outline",
    features: [
      { label: "Up to 3 counties", included: true },
      { label: "Weekly PDF reports", included: true },
      { label: "Ward-level breakdowns", included: false },
      { label: "Automation scheduler", included: false },
      { label: "Priority support", included: false },
    ],
  },
  {
    id: "pro",
    name: "Pro",
    description: "Best for regional teams scaling automated reporting.",
    monthly: 99,
    cta: "Go Pro",
    ctaVariant: "default",
    isPopular: true,
    features: [
      { label: "Up to 15 counties", included: true },
      { label: "Weekly + on-demand reports", included: true },
      { label: "Ward-level breakdowns", included: true },
      { label: "Automation scheduler", included: true },
      { label: "Priority support", included: false },
    ],
  },
  {
    id: "enterprise",
    name: "Enterprise",
    description: "For national coverage with custom workflows and SLAs.",
    monthly: 199,
    cta: "Talk to Sales",
    ctaVariant: "secondary",
    features: [
      { label: "Unlimited counties", included: true },
      { label: "Weekly + on-demand reports", included: true },
      { label: "Ward-level breakdowns", included: true },
      { label: "Automation scheduler", included: true },
      { label: "Dedicated support + SLA", included: true },
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
      "Yes. Annual billing includes a 20% discount across all plans.",
  },
  {
    question: "What's included in Enterprise support?",
    answer:
      "Enterprise includes onboarding, implementation guidance, and a dedicated support channel with an SLA.",
  },
] as const satisfies ReadonlyArray<PricingFaq>
