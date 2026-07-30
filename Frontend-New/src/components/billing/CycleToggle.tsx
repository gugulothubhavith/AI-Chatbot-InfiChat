import { motion } from "framer-motion";
import { useBillingStore, type Cycle } from "@/stores/billing";

export function CycleToggle() {
  const cycle = useBillingStore((s) => s.cycle);
  const setCycle = useBillingStore((s) => s.setCycle);
  const options: { id: Cycle; label: string }[] = [
    { id: "monthly", label: "Monthly" },
    { id: "annually", label: "Annually" },
  ];
  return (
    <div className="relative inline-flex rounded-full border border-border bg-surface p-1 elevated">
      {options.map((o) => {
        const active = cycle === o.id;
        return (
          <button
            key={o.id}
            onClick={() => setCycle(o.id)}
            className="relative z-10 flex items-center gap-1.5 rounded-full px-4 py-1.5 text-xs font-medium"
          >
            {active && (
              <motion.span
                layoutId="cycle-pill"
                className="absolute inset-0 -z-10 rounded-full bg-primary"
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
            <span className={active ? "text-primary-foreground" : "text-muted-foreground"}>{o.label}</span>
            {o.id === "annually" && (
              <span className={`rounded px-1.5 py-0.5 text-[10px] ${active ? "bg-white/15 text-primary-foreground" : "bg-brand/15 text-brand"}`}>
                -20%
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
