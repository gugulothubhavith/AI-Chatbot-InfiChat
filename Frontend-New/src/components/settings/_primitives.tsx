import * as React from "react";
import { motion } from "framer-motion";

export function SectionTitle({ title, description }: { title: string; description?: string }) {
  return (
    <div className="mb-4">
      <h3 className="text-[15px] font-semibold tracking-tight text-foreground">{title}</h3>
      {description && (
        <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
      )}
    </div>
  );
}

export function Row({
  title,
  description,
  children,
  className = "",
}: {
  title: string;
  description?: string;
  children?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`flex items-center justify-between gap-6 py-3.5 ${className}`}>
      <div className="min-w-0">
        <div className="text-[13px] font-medium text-foreground">{title}</div>
        {description && (
          <div className="mt-0.5 text-xs text-muted-foreground">{description}</div>
        )}
      </div>
      {children && <div className="shrink-0">{children}</div>}
    </div>
  );
}

export function Block({ children }: { children: React.ReactNode }) {
  return (
    <div className="divide-y divide-border/60 rounded-xl border border-border/70 bg-surface/40 px-4">
      {children}
    </div>
  );
}

export function TabShell({ children, keyId }: { children: React.ReactNode; keyId: string }) {
  return (
    <motion.div
      key={keyId}
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      transition={{ duration: 0.18, ease: [0.2, 0.8, 0.2, 1] }}
      className="pb-6"
    >
      {children}
    </motion.div>
  );
}
