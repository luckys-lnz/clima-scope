"use client"

import { useId, useState } from "react"
import { Check, Loader2, X } from "lucide-react"

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { cn } from "@/lib/utils"
import { PRICING_FAQS, PRICING_PLANS, type PlanId } from "@/lib/content/pricing"

type BillingCycle = "monthly" | "annual"
type HeadingLevel = "h1" | "h2"

const BILLING_CONFIG = {
  monthly: {
    multiplier: 1,
    label: "Billed monthly",
  },
  annual: {
    multiplier: 12,
    label: "Billed annually",
  },
} as const satisfies Record<BillingCycle, { multiplier: number; label: string }>

const HEADING_STYLES: Record<HeadingLevel, string> = {
  h1: "text-4xl sm:text-5xl font-bold",
  h2: "text-3xl sm:text-4xl font-bold",
}

const USD_TO_KES = 160
const formatKes = (amountKes: number) =>
  new Intl.NumberFormat("en-KE", {
    style: "currency",
    currency: "KES",
    maximumFractionDigits: 0,
  }).format(amountKes)

interface PricingSectionProps {
  id?: string
  headingLevel?: HeadingLevel
  showFaqs?: boolean
  className?: string
}

export function PricingSection({
  id = "pricing",
  headingLevel = "h2",
  showFaqs = true,
  className,
}: PricingSectionProps) {
  const toggleId = useId()
  const [billingCycle, setBillingCycle] = useState<BillingCycle>("monthly")
  const [loadingPlan] = useState<PlanId | null>(null)

  const isAnnual = billingCycle === "annual"
  const HeadingTag = headingLevel

  return (
    <section id={id} className={cn("scroll-mt-24", className)}>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center space-y-4">
          <HeadingTag className={HEADING_STYLES[headingLevel]}>
            Choose your plan
          </HeadingTag>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Flexible pricing for county teams, regional operations, and national
            reporting programs.
          </p>
        </div>

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
            id={toggleId}
            checked={isAnnual}
            onCheckedChange={(checked) => {
              setBillingCycle(checked ? "annual" : "monthly")
            }}
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
          </div>
        </div>

        <div className="mt-10 flex justify-center">
          {PRICING_PLANS.map((plan) => {
            const priceUsd = plan.monthly * BILLING_CONFIG[billingCycle].multiplier
            const priceKes = Math.round(priceUsd * USD_TO_KES)
            const isLoading = loadingPlan === plan.id

            return (
              <Card
                key={plan.id}
                className="w-full max-w-md"
              >
                <CardHeader>
                  <div className="space-y-2">
                    <CardTitle className="text-xl">{plan.name}</CardTitle>
                    <CardDescription>{plan.description}</CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 space-y-6">
                  <div className="space-y-2">
                    <div className="flex items-end gap-2">
                      <span className="text-4xl font-semibold">
                        {formatKes(priceKes)}
                      </span>
                      <span className="text-sm text-muted-foreground">
                        {isAnnual ? "/year" : "/month"}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {BILLING_CONFIG[billingCycle].label}
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
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-2 text-xs text-muted-foreground">
          <span>Cancel anytime</span>
          <span aria-hidden>&middot;</span>
          <span>No credit card required</span>
          <span aria-hidden>&middot;</span>
          <span>Secure payments</span>
        </div>

        {showFaqs && (
          <div className="mt-16">
            <div className="max-w-3xl mx-auto">
              <div className="text-center space-y-2">
                <h3 className="text-2xl font-semibold">Frequently asked questions</h3>
                <p className="text-muted-foreground">
                  Answers to common questions about billing, upgrades, and usage.
                </p>
              </div>
              <Accordion type="single" collapsible className="mt-8">
                {PRICING_FAQS.map((faq, index) => (
                  <AccordionItem key={faq.question} value={`faq-${index}`}>
                    <AccordionTrigger>{faq.question}</AccordionTrigger>
                    <AccordionContent>{faq.answer}</AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
