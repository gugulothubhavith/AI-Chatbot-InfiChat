import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { motion } from "framer-motion";
import { tapProps } from "@/lib/motion";
import { useBillingStore } from "@/stores/billing";
import { toast } from "sonner";
import { useState } from "react";
import { Loader2 } from "lucide-react";

export function UpgradeDialog({ planId, onOpenChange }: { planId: string | null; onOpenChange: (v: boolean) => void }) {
  const cycle = useBillingStore((s) => s.cycle);
  const checkout = useBillingStore((s) => s.checkout);
  const availablePlans = useBillingStore((s) => s.availablePlans);
  
  const [loading, setLoading] = useState(false);

  const plan = availablePlans.find(p => p.id === planId);
  const price = plan ? (cycle === "annually" ? plan.regional.annual / 12 : plan.regional.monthly) : 0;
  const total = cycle === "annually" ? price * 12 : price;
  const symbol = plan?.regional.symbol || "$";

  return (
    <Dialog open={!!planId} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogTitle className="text-lg font-medium tracking-tight capitalize">Upgrade to {plan?.name}</DialogTitle>
        <DialogDescription className="text-xs text-muted-foreground">
          Review your order before confirming.
        </DialogDescription>

        <div className="mt-4 rounded-xl border border-border bg-surface-2/40 p-4 text-sm">
          <div className="flex items-center justify-between py-1">
            <span className="text-muted-foreground capitalize">{plan?.name} plan</span>
            <span>{symbol}{price}/mo</span>
          </div>
          <div className="flex items-center justify-between py-1">
            <span className="text-muted-foreground">Billing</span>
            <span className="capitalize">{cycle}</span>
          </div>
          <div className="mt-2 border-t border-border pt-2 flex items-center justify-between font-medium">
            <span>Total today</span>
            <span>{symbol}{total.toFixed(2)}</span>
          </div>
        </div>

        <div className="mt-4 space-y-2">
          <label className="text-xs text-muted-foreground">Card number</label>
          <input className="h-10 w-full rounded-lg border border-border bg-surface px-3 font-mono text-sm outline-none focus-visible:shadow-[0_0_0_2px_var(--background),0_0_0_4px_color-mix(in_oklab,var(--brand)_60%,transparent)]" placeholder="4242 4242 4242 4242" />
          <div className="grid grid-cols-2 gap-2">
            <input className="h-10 rounded-lg border border-border bg-surface px-3 font-mono text-sm outline-none" placeholder="MM / YY" />
            <input className="h-10 rounded-lg border border-border bg-surface px-3 font-mono text-sm outline-none" placeholder="CVC" />
          </div>
        </div>

        <motion.button
          {...tapProps}
          disabled={loading}
          onClick={async () => {
            if (planId) {
              setLoading(true);
              await checkout(planId, cycle);
              setLoading(false);
            }
            toast.success(`You're on the ${plan?.name} plan`);
            onOpenChange(false);
          }}
          className="mt-4 flex h-10 w-full items-center justify-center rounded-lg bg-primary text-sm font-medium text-primary-foreground elevated disabled:opacity-50"
        >
          {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Confirm payment · {symbol}{total.toFixed(2)}
        </motion.button>
        <div className="mt-2 text-center text-[11px] text-muted-foreground">Secured by InfiChat · Cancel anytime</div>
      </DialogContent>
    </Dialog>
  );
}
