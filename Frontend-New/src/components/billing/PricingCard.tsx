import { motion } from "framer-motion";
import { tapProps } from "@/lib/motion";
import { Check } from "lucide-react";
import { useBillingStore } from "@/stores/billing";

export function PricingCard({
  planId,
  name,
  tag,
  priceMonthly,
  priceAnnual,
  symbol,
  description,
  features,
  highlight,
  dark,
  onUpgrade,
}: {
  planId: string;
  name: string;
  tag?: string;
  priceMonthly: number;
  priceAnnual: number;
  symbol: string;
  description: string;
  features: string[];
  highlight?: boolean;
  dark?: boolean;
  onUpgrade: () => void;
}) {
  const currentPlanId = useBillingStore((s) => s.currentPlanId);
  const cycle = useBillingStore((s) => s.cycle);
  const isCurrent = currentPlanId === planId;
  const price = cycle === "annually" ? priceAnnual : priceMonthly;

  return (
    <motion.div
      whileHover={{ y: -3 }}
      transition={{ type: "spring", stiffness: 400, damping: 30 }}
      className={`relative flex flex-col rounded-2xl border p-6 ${
        dark
          ? "bg-[#0a0a0a] text-white border-white/10"
          : highlight
            ? "border-brand/50 bg-surface elevated"
            : "border-border bg-surface"
      }`}
      style={
        highlight
          ? { boxShadow: "0 0 0 1px color-mix(in oklab, var(--brand) 40%, transparent), 0 20px 60px -20px color-mix(in oklab, var(--brand) 40%, transparent), inset 0 1px 0 color-mix(in oklab, white 8%, transparent)" }
          : undefined
      }
    >
      {highlight && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-brand px-3 py-1 text-[10px] font-medium uppercase tracking-wider text-brand-foreground">
          Most Popular
        </div>
      )}
      <div className="mb-1 flex items-center justify-between">
        <div className="text-sm font-medium">{name}</div>
        {isCurrent && (
          <div className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${dark ? "bg-white/10" : "bg-emerald-500/15 text-emerald-500"}`}>
            Active Plan
          </div>
        )}
      </div>
      <p className={`text-xs ${dark ? "text-white/60" : "text-muted-foreground"}`}>{description}</p>
      <div className="mt-6 flex items-baseline gap-1">
        <span className="text-5xl font-medium tracking-tight">{symbol}{price}</span>
        <span className={`text-xs ${dark ? "text-white/50" : "text-muted-foreground"}`}>
          /{cycle === "annually" ? "mo, billed yearly" : "mo"}
        </span>
      </div>
      {tag && <div className={`mt-1 text-[11px] ${dark ? "text-white/50" : "text-muted-foreground"}`}>{tag}</div>}
      <ul className="mt-6 flex-1 space-y-2.5 text-sm">
        {features.map((f) => (
          <li key={f} className="flex items-start gap-2">
            <span className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full ${dark ? "bg-white/10" : highlight ? "bg-brand/15" : "bg-emerald-500/15"}`}>
              <Check className={`h-2.5 w-2.5 ${dark ? "text-white" : highlight ? "text-brand" : "text-emerald-600"}`} />
            </span>
            <span className={dark ? "text-white/85" : ""}>{f}</span>
          </li>
        ))}
      </ul>
      <motion.button
        {...tapProps}
        disabled={isCurrent}
        onClick={onUpgrade}
        className={`mt-6 flex h-10 items-center justify-center rounded-lg text-sm font-medium ${
          isCurrent
            ? dark ? "bg-white/5 text-white/50" : "bg-surface-2 text-muted-foreground"
            : highlight
              ? "bg-brand text-brand-foreground elevated"
              : dark
                ? "bg-white text-black"
                : "bg-primary text-primary-foreground elevated"
        }`}
      >
        {isCurrent ? "Current plan" : name === "Enterprise" ? "Contact sales" : "Upgrade"}
      </motion.button>
    </motion.div>
  );
}
