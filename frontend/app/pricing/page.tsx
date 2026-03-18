"use client"

import { useState } from "react"
import { Check, Loader2, X } from "lucide-react"

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"

type PlanId = "starter" | "pro" | "enterprise"

type Plan = {
  id: PlanId
  name: string
  description: string
  monthly: number
  cta: string
  ctaVariant: "default" | "outline" | "secondary"
  isPopular?: boolean
  features: { label: string; included: boolean }[]
}

const plans: Plan[] = [
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
]

const faqs = [
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
]

export default function PricingPage() {
  const [isAnnual, setIsAnnual] = useState(false)
  const [loadingPlan] = useState<PlanId | null>(null)

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-16">
        <section className="text-center space-y-4">
          <h1 className="text-4xl sm:text-5xl font-bold">Choose your plan</h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Flexible pricing for county teams, regional operations, and national
            reporting programs.
          </p>
        </section>

        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
          <span
            className={cn(
              "text-sm font-medium",
              isAnnual ? "text-muted-foreground" : "text-foreground",
            )}
          >
            Monthly
          </span>
          <Switch
            id="billing-toggle"
            checked={isAnnual}
            onCheckedChange={setIsAnnual}
            aria-label="Toggle annual billing"
          />
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "text-sm font-medium",
                isAnnual ? "text-foreground" : "text-muted-foreground",
              )}
            >
              Annual
            </span>
            {isAnnual && <Badge variant="secondary">Save 20%</Badge>}
          </div>
        </div>

        <section className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {plans.map((plan) => {
            const price = isAnnual
              ? Math.round(plan.monthly * 0.8)
              : plan.monthly
            const isLoading = loadingPlan === plan.id

            return (
              <Card
                key={plan.id}
                className={cn(
                  "h-full",
                  plan.isPopular && "ring-2 ring-primary",
                )}
              >
                <CardHeader>
                  <div className="space-y-2">
                    <CardTitle className="text-xl">{plan.name}</CardTitle>
                    <CardDescription>{plan.description}</CardDescription>
                  </div>
                  {plan.isPopular && (
                    <CardAction>
                      <Badge>Most Popular</Badge>
                    </CardAction>
                  )}
                </CardHeader>
                <CardContent className="flex-1 space-y-6">
                  <div className="space-y-2">
                    <div className="flex items-end gap-2">
                      <span className="text-4xl font-semibold">${price}</span>
                      <span className="text-sm text-muted-foreground">
                        /month
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {isAnnual ? "Billed annually" : "Billed monthly"}
                    </p>
                  </div>
                  <ul className="space-y-3">
                    {plan.features.map((feature) => (
                      <li
                        key={feature.label}
                        className="flex items-start gap-3 text-sm"
                      >
                        {feature.included ? (
                          <Check className="size-4 text-primary" />
                        ) : (
                          <X className="size-4 text-muted-foreground" />
                        )}
                        <span
                          className={cn(
                            feature.included
                              ? "text-foreground"
                              : "text-muted-foreground",
                          )}
                        >
                          {feature.label}
                        </span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
                <CardFooter className="mt-auto">
                  <Button
                    className="w-full"
                    variant={plan.ctaVariant}
                    disabled={isLoading}
                    onClick={() => {
                      // TODO: wire up payment provider
                    }}
                  >
                    {isLoading ? (
                      <span className="flex items-center gap-2">
                        <Loader2 className="size-4 animate-spin" />
                        Processing...
                      </span>
                    ) : (
                      plan.cta
                    )}
                  </Button>
                </CardFooter>
              </Card>
            )
          })}
        </section>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-2 text-xs text-muted-foreground">
          <span>Cancel anytime</span>
          <span aria-hidden>&middot;</span>
          <span>No credit card required</span>
          <span aria-hidden>&middot;</span>
          <span>Secure payments</span>
        </div>

        <section className="mt-16">
          <div className="max-w-3xl mx-auto">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-semibold">Frequently asked questions</h2>
              <p className="text-muted-foreground">
                Answers to common questions about billing, upgrades, and usage.
              </p>
            </div>
            <Accordion type="single" collapsible className="mt-8">
              {faqs.map((faq, index) => (
                <AccordionItem key={faq.question} value={`faq-${index}`}>
                  <AccordionTrigger>{faq.question}</AccordionTrigger>
                  <AccordionContent>{faq.answer}</AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
        </section>
      </div>
    </main>
  )
}
