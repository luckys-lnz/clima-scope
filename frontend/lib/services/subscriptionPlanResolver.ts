import { PRICING_PLANS, type PricingPlan } from "@/lib/content/pricing";
import type { SubscriptionPlan } from "@/lib/services/subscriptionService";

export type BillingCycle = "monthly" | "annual";

export const getPriceForCycle = (
  plan: PricingPlan,
  cycle: BillingCycle,
): number => (cycle === "annual" ? plan.annual : plan.monthly);

export const resolveBackendPlan = (
  plans: SubscriptionPlan[],
  cycle: BillingCycle,
): SubscriptionPlan | null => {
  const targetAmount = getPriceForCycle(PRICING_PLANS[0], cycle);
  const targetCycle = cycle === "annual" ? "yearly" : "monthly";

  const exact = plans.find((p) => {
    const price = Number(p.price);
    const billing = String(p.billing_cycle || "")
      .trim()
      .toLowerCase();
    const currency = String(p.currency || "")
      .trim()
      .toUpperCase();
    return (
      price === targetAmount && billing === targetCycle && currency === "KES"
    );
  });
  if (exact) return exact;

  const cycleOnly = plans.find(
    (p) =>
      String(p.billing_cycle || "")
        .trim()
        .toLowerCase() === targetCycle,
  );
  if (cycleOnly) return cycleOnly;

  const priceOnly = plans.find((p) => Number(p.price) === targetAmount);
  if (priceOnly) return priceOnly;

  return plans[0] ?? null;
};
