import { createFileRoute } from "@tanstack/react-router";
import { PricingCard } from "@/components/billing/PricingCard";
import { CycleToggle } from "@/components/billing/CycleToggle";
import { UpgradeDialog } from "@/components/billing/UpgradeDialog";
import { useState } from "react";
import { useBillingStore } from "@/stores/billing";
import { Logo } from "@/components/brand/Logo";

export const Route = createFileRoute("/_app/billing")({
  head: () => ({
    meta: [
      { title: "Billing — InfiChat" },
      { name: "description", content: "Choose the plan that fits your team." },
      { property: "og:title", content: "Billing — InfiChat" },
      { property: "og:description", content: "Choose the plan that fits your team." },
    ],
  }),
  component: BillingPage,
});

function BillingPage() {
  const [upgradeId, setUpgradeId] = useState<string | null>(null);
  const availablePlans = useBillingStore((s) => s.availablePlans);
  const cycle = useBillingStore((s) => s.cycle);
  const checkout = useBillingStore((s) => s.checkout);

  return (
    <div className="relative h-full overflow-y-auto">
      <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex justify-start pt-4 pl-5">
        <span className="select-none font-bold text-foreground leading-none" style={{ fontSize: 18, letterSpacing: "-0.015em" }}>InfiChat</span>
      </div>
      <div className="mx-auto max-w-6xl px-8 py-16">

        <div className="mb-2 text-center text-xs text-muted-foreground">Plans & Billing</div>
        <h1 className="text-center text-4xl font-medium tracking-tight">Simple, scalable pricing</h1>
        <p className="mx-auto mt-3 max-w-lg text-center text-sm text-muted-foreground">
          Start free. Upgrade as your team grows. Cancel anytime.
        </p>
        <div className="mt-8 flex justify-center">
          <CycleToggle />
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {availablePlans.map((p) => {
            const isHighlight = p.name === "Pro" || p.name === "Max";
            const isDark = p.name === "Enterprise";
            
            // Format limits as features for display
            const limits = p.limits || {};
            const features = [
              `${limits.chat_messages_per_day > 900000 ? "Unlimited" : limits.chat_messages_per_day} messages / day`,
              `${limits.max_context_length > 900000 ? "Unlimited" : (limits.max_context_length / 1000).toFixed(0) + "k"} token context`,
              `${limits.rag_documents > 900000 ? "Unlimited" : limits.rag_documents} RAG documents`,
              `${limits.deep_research_per_month > 900000 ? "Unlimited" : limits.deep_research_per_month} deep research / mo`,
              `${limits.web_search_per_month > 900000 ? "Unlimited" : limits.web_search_per_month} web searches / mo`,
            ];

            return (
              <PricingCard
                key={p.id}
                planId={p.id}
                name={p.name}
                priceMonthly={p.regional.monthly}
                priceAnnual={p.regional.annual / 12}
                symbol={p.regional.symbol}
                description={p.description || "InfiChat subscription tier"}
                features={features}
                highlight={isHighlight}
                dark={isDark}
                onUpgrade={() => {
                  checkout(p.id, cycle);
                }}
              />
            );
          })}
        </div>
      </div>
      <UpgradeDialog planId={upgradeId} onOpenChange={(v) => !v && setUpgradeId(null)} />
    </div>
  );
}
