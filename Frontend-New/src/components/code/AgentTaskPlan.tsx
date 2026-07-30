import { motion } from "framer-motion";
import { Check, Loader2 } from "lucide-react";
import type { PlanNode } from "@/hooks/useCodeSquad";

export function AgentTaskPlan({ plan }: { plan: PlanNode[] }) {
  return (
    <div className="space-y-3">
      {plan.map((node, i) => (
        <motion.div
          key={node.id}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
          className="overflow-hidden rounded-xl border border-border bg-surface-2/40"
        >
          <div className="flex items-center gap-2 border-b border-border/60 px-3 py-2">
            <NodeStatus status={node.status} />
            <div className="min-w-0 flex-1 truncate text-[12px] font-medium tracking-tight">{node.title}</div>
            <span className="shrink-0 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              {node.children?.length ?? 0} tasks
            </span>
          </div>

          <div className="grid gap-1 p-2">
            {node.children?.map((child) => (
              <motion.div
                key={child.id}
                layout
                className={`relative flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-[12px] ${
                  child.status === "running" ? "bg-brand/10" : ""
                }`}
              >
                {child.status === "running" && (
                  <motion.span
                    className="absolute inset-0 rounded-lg ring-1 ring-brand/40"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1.4, repeat: Infinity }}
                  />
                )}
                <NodeStatus status={child.status} />
                <span className="relative">{child.title}</span>
              </motion.div>
            ))}
          </div>
        </motion.div>
      ))}
    </div>
  );
}

function NodeStatus({ status }: { status?: PlanNode["status"] }) {
  if (status === "completed") {
    return (
      <span className="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-500">
        <Check className="h-2.5 w-2.5" strokeWidth={3} />
      </span>
    );
  }
  if (status === "running") {
    return <Loader2 className="h-3.5 w-3.5 animate-spin text-brand" />;
  }
  return <span className="h-2 w-2 rounded-full bg-muted-foreground/30" />;
}
