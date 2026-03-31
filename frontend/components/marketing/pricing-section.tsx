"use client"

import { useId, useState } from "react"
import { useRouter } from "next/navigation"
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
import { useAuth } from "@/hooks/useAuth"
import { cn } from "@/lib/utils"
import { PRICING_FAQS, PRICING_PLANS, type PlanId } from "@/lib/content/pricing"
import { subscriptionService, type SubscriptionPlan } from "@/lib/services/subscriptionService"

type BillingCycle = "monthly" | "annual"
type HeadingLevel = "h1" | "h2"

const BILLING_CONFIG = {
  monthly: {
    amount: 1000,
    label: "Billed monthly",
    period: "/month",
  },
  annual: {
    amount: 10000,
    label: "Billed yearly",
    period: "/year",
  },
} as const satisfies Record<BillingCycle, { amount: number; label: string; period: string }>

const HEADING_STYLES: Record<HeadingLevel, string> = {
  h1: "text-4xl sm:text-5xl font-bold",
  h2: "text-3xl sm:text-4xl font-bold",
}

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
  const router = useRouter()
  const { access_token } = useAuth()
  const toggleId = useId()
  const [billingCycle, setBillingCycle] = useState<BillingCycle>("monthly")
  const [loadingPlan, setLoadingPlan] = useState<PlanId | null>(null)
  const [errorMessage, setErrorMessage] = useState<string>("")

  const isAnnual = billingCycle === "annual"
  const HeadingTag = headingLevel

  const resolveBackendPlan = (plans: SubscriptionPlan[], cycle: BillingCycle): SubscriptionPlan | null => {
    const targetAmount = BILLING_CONFIG[cycle].amount
    const targetCycle = cycle === "annual" ? "yearly" : "monthly"

    const exact = plans.find((p) => {
      const price = Number(p.price)
      const billing = String(p.billing_cycle || "").trim().toLowerCase()
      const currency = String(p.currency || "").trim().toUpperCase()
      return price === targetAmount && billing === targetCycle && currency === "KES"
    })
    if (exact) return exact

    const cycleOnly = plans.find((p) => String(p.billing_cycle || "").trim().toLowerCase() === targetCycle)
    if (cycleOnly) return cycleOnly

    const priceOnly = plans.find((p) => Number(p.price) === targetAmount)
    if (priceOnly) return priceOnly

    return plans[0] ?? null
  }

  const handleCheckout = async (planId: PlanId): Promise<void> => {
    setErrorMessage("")
    if (!access_token) {
      router.push("/sign-in")
      return
    }

    try {
      setLoadingPlan(planId)
      const plans = await subscriptionService.getPlans(access_token)
      const backendPlan = resolveBackendPlan(plans, billingCycle)
      if (!backendPlan) {
        throw new Error("No matching backend subscription plan found. Please contact support.")
      }

      const checkout = await subscriptionService.startCheckout(access_token, {
        plan_id: backendPlan.id,
        return_url: typeof window !== "undefined" ? window.location.href : undefined,
        description: `${backendPlan.name} subscription`,
      })

      if (!checkout.redirect_url) {
        throw new Error("Pesapal checkout URL was not returned.")
      }

      window.location.href = checkout.redirect_url
    } catch (error: any) {
      setErrorMessage(error?.message || "Failed to initialize payment.")
    } finally {
      setLoadingPlan(null)
    }
  }

  return (
    <section id={id} className={className}>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center space-y-4">
          <HeadingTag className={HEADING_STYLES[headingLevel]}>
            Choose your plan
          </HeadingTag>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Simple pricing for weather reporting operations.
          </p>
        </div>

        <div className="mt-10 flex items-center justify-center">
          <div className="inline-flex items-center gap-3 rounded-xl border border-zinc-500/70 bg-zinc-900/40 px-4 py-2 shadow-sm">
            <span
              className={cn(
                "text-sm font-medium transition-colors",
                isAnnual ? "text-zinc-400" : "text-zinc-100",
              )}
            >
              Monthly
            </span>
            <Switch
              id={toggleId}
              className="border-zinc-400/80 data-[state=unchecked]:bg-zinc-700 data-[state=checked]:bg-emerald-500 focus-visible:ring-emerald-300/40"
              checked={isAnnual}
              onCheckedChange={(checked) => {
                setBillingCycle(checked ? "annual" : "monthly")
              }}
              aria-label="Toggle annual billing"
            />
            <div className="flex items-center gap-2">
            <span
              className={cn(
                "text-sm font-medium transition-colors",
                isAnnual ? "text-zinc-100" : "text-zinc-400",
              )}
            >
              Annual
            </span>
            {isAnnual && <Badge variant="secondary">Save 16.67%</Badge>}
            </div>
          </div>
        </div>

        <div className="mt-12 max-w-3xl mx-auto">
          {PRICING_PLANS.map((plan) => {
            const price = BILLING_CONFIG[billingCycle].amount
            const isLoading = loadingPlan === plan.id
            const isPopularOffer = isAnnual
            const isGoProDisabled = plan.id === "pro"

            return (
              <Card
                key={plan.id}
                className={cn(
                  "w-full rounded-2xl border-border/70 shadow-sm",
                  isPopularOffer && "ring-2 ring-primary",
                )}
              >
                <CardHeader className="pb-3 md:pb-4 px-6 pt-6 md:px-8 md:pt-8">
                  <div className="space-y-2">
                    <CardTitle className="text-2xl">{plan.name}</CardTitle>
                    <CardDescription className="text-sm md:text-base">{plan.description}</CardDescription>
                  </div>
                  {isPopularOffer && (
                    <CardAction>
                      <Badge>Most Popular</Badge>
                    </CardAction>
                  )}
                </CardHeader>
                <CardContent className="flex-1 grid gap-8 md:grid-cols-2 px-6 py-2 md:px-8">
                  <div className="space-y-3">
                    <div className="flex items-end gap-2">
                      <span className="text-5xl font-semibold tracking-tight">KES {price.toLocaleString()}</span>
                      <span className="text-sm text-muted-foreground">
                        {BILLING_CONFIG[billingCycle].period}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {BILLING_CONFIG[billingCycle].label}
                    </p>
                    {isAnnual && (
                      <p className="text-sm font-medium text-primary">You save 16.67% on yearly billing.</p>
                    )}
                  </div>
                  <ul className="space-y-3 md:pt-1">
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
                <CardFooter className="mt-auto px-6 pb-6 pt-4 md:px-8 md:pb-8">
                  <Button
                    className="w-full h-11"
                    variant={plan.ctaVariant}
                    disabled={isLoading || isGoProDisabled}
                    onClick={() => {
                      if (isGoProDisabled) return
                      void handleCheckout(plan.id)
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

        {errorMessage && (
          <div className="mt-6 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-600">
            {errorMessage}
          </div>
        )}

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
