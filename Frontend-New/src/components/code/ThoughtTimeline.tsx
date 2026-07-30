import { Check, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export function ThoughtTimeline({ steps }: { steps: { step: string; status: "done" | "active" | "pending" }[] }) {
  return (
    <div className="mb-3 rounded-xl border border-border bg-surface-2/40 p-3">
      <div className="mb-2 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
        Thought process
      </div>
      <div className="space-y-1.5">
        {steps.map((s, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -4 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-center gap-2 text-[13px]"
          >
            <div
              className={`flex h-5 w-5 items-center justify-center rounded-full ${
                s.status === "done"
                  ? "bg-emerald-500/15 text-emerald-500"
                  : s.status === "active"
                    ? "bg-brand/15 text-brand"
                    : "bg-surface text-muted-foreground"
              }`}
            >
              {s.status === "done" ? (
                <Check className="h-3 w-3" />
              ) : s.status === "active" ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <span className="text-[9px]">{i + 1}</span>
              )}
            </div>
            <span className={s.status === "pending" ? "text-muted-foreground" : ""}>{s.step}</span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
