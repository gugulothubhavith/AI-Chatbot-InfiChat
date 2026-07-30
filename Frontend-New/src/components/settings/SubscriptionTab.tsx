import { useState } from "react";
import { Block, Row, SectionTitle, TabShell } from "./_primitives";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useBillingStore, type ApiPlan } from "@/stores/billing";
import { api } from "@/lib/api";
import {
  Crown,
  ExternalLink,
  CreditCard,
  Receipt,
  ShieldCheck,
  Loader2,
  ChevronLeft,
  Download,
  Check,
} from "lucide-react";
import { toast } from "sonner";
import { generateInvoicePdf } from "@/lib/invoicePdf";
import { useAuthStore } from "@/stores/auth";
import { useNavigate } from "@tanstack/react-router";
import { useSettingsDialog } from "@/components/shell/settings-context";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const getGradient = (name: string) => {
  if (name === "Free") return "from-slate-500/25 to-slate-500/5";
  if (name === "Starter") return "from-blue-500/30 to-blue-500/5";
  if (name === "Pro") return "from-brand/30 to-brand/5";
  if (name === "Max") return "from-purple-500/30 to-purple-500/5";
  return "from-amber-500/30 to-amber-500/5"; // Enterprise
};

type PortalView = "root" | "payment" | "invoices" | "plan";

export function SubscriptionTab() {
  const currentPlanId = useBillingStore((s) => s.currentPlanId);
  const availablePlans = useBillingStore((s) => s.availablePlans);
  const checkout = useBillingStore((s) => s.checkout);
  const cycle = useBillingStore((s) => s.cycle);
  const setCycle = useBillingStore((s) => s.setCycle);
  const paymentMethod = useBillingStore((s) => s.paymentMethod);
  const setPaymentMethod = useBillingStore((s) => s.setPaymentMethod);
  const invoices = useBillingStore((s) => s.invoices);
  const { setOpen: setSettingsOpen } = useSettingsDialog();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);
  const [portalOpen, setPortalOpen] = useState(false);
  const [view, setView] = useState<PortalView>("root");

  const openPortal = async () => {
    setLoading(true);
    try {
        const res = await api.getPortalUrl() as any;
        if (res?.url) {
            window.location.href = res.url;
        } else {
            toast.error("Billing portal not available");
        }
    } catch (e) {
        toast.error("Failed to open billing portal");
    } finally {
        setLoading(false);
    }
  };

  const activePlan = availablePlans.find(p => p.id === currentPlanId) || availablePlans.find(p => p.name === "Free") || {
    id: "free", name: "Free", description: "For personal exploration",
    regional: { symbol: "$", monthly: 0, annual: 0, currency: "USD" }
  } as unknown as ApiPlan;

  const gradient = getGradient(activePlan.name);

  return (
    <TabShell keyId="subscription">
      <SectionTitle title="Current plan" description="Manage your subscription and billing." />
      <div className="mb-6">
        <div className={`flex flex-col gap-4 overflow-hidden rounded-xl border border-border/70 bg-gradient-to-br ${gradient} p-4 sm:flex-row sm:items-center sm:justify-between`}>
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-background/50 shadow-sm backdrop-blur-xl">
              <Crown className="h-6 w-6 text-foreground" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="border-foreground/20 bg-background/50 px-1.5 py-0 text-[10px] uppercase tracking-wider backdrop-blur-xl">
                  {cycle}
                </Badge>
              </div>
              <div className="text-xl font-semibold tracking-tight">{activePlan.name} Plan</div>
              <div className="mt-1 text-xs text-muted-foreground">{activePlan.description}</div>
            </div>
          </div>
          <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => { setView("plan"); setPortalOpen(true); }}>
                Change Plan
              </Button>
              <Button size="sm" onClick={openPortal} disabled={loading}>
                {loading ? (
                  <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                ) : (
                  <ExternalLink className="mr-1.5 h-3.5 w-3.5" />
                )}
                Manage Billing
              </Button>
          </div>
        </div>
      </div>

      <Dialog open={portalOpen} onOpenChange={setPortalOpen}>
        <DialogContent className="sm:max-w-md">
          {view === "plan" && (
            <PlanView
              currentId={currentPlanId}
              onBack={() => setPortalOpen(false)}
              onSelect={async (p) => {
                await checkout(p, cycle);
                toast("Redirecting to checkout...");
              }}
              onOpenPricing={() => {
                setPortalOpen(false);
                setSettingsOpen(false);
                navigate({ to: "/billing" });
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </TabShell>
  );
}

function PlanView({
  currentId,
  onBack,
  onSelect,
  onOpenPricing,
}: {
  currentId: string | null;
  onBack: () => void;
  onSelect: (p: string) => void;
  onOpenPricing: () => void;
}) {
  const availablePlans = useBillingStore((s) => s.availablePlans);
  const cycle = useBillingStore((s) => s.cycle);
  
  return (
    <>
      <DialogHeader>
        <button onClick={onBack} className="mb-1 flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground">
          <ChevronLeft className="h-3 w-3" /> Back
        </button>
        <DialogTitle>Change or cancel plan</DialogTitle>
        <DialogDescription>Switch instantly — prorated automatically.</DialogDescription>
      </DialogHeader>
      <div className="space-y-2">
        {availablePlans.map((p) => {
          const isCurrent = p.id === currentId;
          const price = cycle === "monthly" ? p.regional.monthly : p.regional.annual;
          
          return (
            <button
              key={p.id}
              onClick={() => !isCurrent && onSelect(p.id)}
              disabled={isCurrent}
              className={`flex w-full items-center gap-3 rounded-lg border p-3 text-left transition-colors ${
                isCurrent ? "border-brand/60 bg-brand/5" : "border-border hover:bg-surface-2"
              }`}
            >
              <div className={`flex h-8 w-8 items-center justify-center rounded-md ${isCurrent ? "bg-brand/15 text-brand" : "bg-surface-2 text-muted-foreground"}`}>
                <Crown className="h-4 w-4" />
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium">{p.name} Plan</div>
                <div className="text-[11px] text-muted-foreground">{p.description || "InfiChat subscription tier"}</div>
              </div>
              <div className="text-right">
                <div className="text-sm font-mono">{p.regional.symbol}{price}<span className="text-[10px] text-muted-foreground">/{cycle === "monthly" ? "mo" : "yr"}</span></div>
                {isCurrent && (
                  <div className="mt-0.5 flex items-center justify-end gap-1 text-[10px] text-brand">
                    <Check className="h-3 w-3" /> Current
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>
      <DialogFooter className="flex-col gap-2 sm:flex-row sm:justify-between">
        <Button variant="ghost" size="sm" onClick={onOpenPricing}>
          Compare all plans
        </Button>
        <Button variant="outline" size="sm" onClick={onBack}>Close</Button>
      </DialogFooter>
    </>
  );
}
