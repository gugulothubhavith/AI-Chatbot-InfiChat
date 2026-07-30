import { useState } from "react";
import { SectionTitle, TabShell } from "./_primitives";
import { Button } from "@/components/ui/button";
import { RefreshCw, Check } from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "sonner";

export function UpdatesTab() {
  const [checking, setChecking] = useState(false);
  const [status, setStatus] = useState<"idle" | "current">("idle");

  const check = () => {
    setChecking(true);
    setStatus("idle");
    setTimeout(() => {
      setChecking(false);
      setStatus("current");
      toast.success("You're up to date", { description: "InfiChat v0.1.0" });
    }, 1400);
  };

  return (
    <TabShell keyId="updates">
      <SectionTitle title="Updates" description="Stay on the latest version of InfiChat." />
      <div className="flex flex-col items-center justify-center rounded-2xl border border-border/70 bg-surface/40 px-6 py-10 text-center">
        <div className="relative mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-brand/10">
          <div className="absolute inset-0 rounded-full bg-brand/10 blur-xl" />
          <motion.div animate={checking ? { rotate: 360 } : { rotate: 0 }} transition={checking ? { repeat: Infinity, duration: 1, ease: "linear" } : { duration: 0.3 }}>
            {status === "current" && !checking ? (
              <Check className="h-8 w-8 text-brand" />
            ) : (
              <RefreshCw className="h-8 w-8 text-brand" />
            )}
          </motion.div>
        </div>
        <div className="text-[15px] font-semibold">InfiChat v0.1.0</div>
        <div className="mt-1 text-xs text-muted-foreground">
          {checking ? "Checking for updates…" : status === "current" ? "You're on the latest version." : "Last checked a few minutes ago."}
        </div>
        <Button className="mt-5" onClick={check} disabled={checking}>
          {checking ? "Checking…" : "Check for updates"}
        </Button>
      </div>
    </TabShell>
  );
}
