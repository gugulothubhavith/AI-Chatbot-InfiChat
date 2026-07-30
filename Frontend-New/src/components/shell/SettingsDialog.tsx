import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { useState } from "react";
import { AnimatePresence } from "framer-motion";
import { Settings2, Bell, Sparkles, Database, Shield, RefreshCw, User, CreditCard } from "lucide-react";
import { GeneralTab } from "@/components/settings/GeneralTab";
import { NotificationsTab } from "@/components/settings/NotificationsTab";
import { PersonalizationTab } from "@/components/settings/PersonalizationTab";
import { DataControlsTab } from "@/components/settings/DataControlsTab";
import { SecurityTab } from "@/components/settings/SecurityTab";
import { UpdatesTab } from "@/components/settings/UpdatesTab";
import { AccountTab } from "@/components/settings/AccountTab";
import { SubscriptionTab } from "@/components/settings/SubscriptionTab";

const tabs = [
  { id: "general", label: "General", icon: Settings2 },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "personalization", label: "Personalization", icon: Sparkles },
  { id: "data", label: "Data controls", icon: Database },
  { id: "security", label: "Security", icon: Shield },
  { id: "updates", label: "Updates", icon: RefreshCw },
  { id: "account", label: "Account", icon: User },
  { id: "subscription", label: "Subscription", icon: CreditCard },
] as const;

type TabId = (typeof tabs)[number]["id"];

export function SettingsDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  const [tab, setTab] = useState<TabId>("general");
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="gap-0 overflow-hidden border border-border/60 bg-white p-0 shadow-2xl backdrop-blur-2xl dark:bg-[#212121] sm:max-w-[740px]"
        style={{ height: 580 }}
      >
        <DialogTitle className="sr-only">Settings</DialogTitle>
        <DialogDescription className="sr-only">Manage your InfiChat preferences.</DialogDescription>

        <div className="grid h-full min-h-0 grid-cols-[210px_1fr] grid-rows-1">
          <aside className="flex min-h-0 flex-col border-r border-border/60 bg-surface-2/30 px-2 py-3">
            <div className="px-2.5 pb-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Settings
            </div>
            <nav className="settings-scroll flex-1 min-h-0 space-y-0.5 overflow-y-auto">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`flex h-8 w-full items-center gap-2.5 rounded-md px-2.5 text-[13px] transition-colors ${
                    tab === t.id
                      ? "bg-sidebar-accent text-foreground"
                      : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground"
                  }`}
                >
                  <t.icon className="h-3.5 w-3.5" />
                  {t.label}
                </button>
              ))}
            </nav>
            <div className="px-2.5 pt-3 text-[10px] text-muted-foreground">InfiChat v0.1.0</div>
          </aside>

          <div className="settings-scroll min-h-0 h-full overflow-y-auto px-8 py-7">
            <AnimatePresence mode="wait">
              {tab === "general" && <GeneralTab />}
              {tab === "notifications" && <NotificationsTab />}
              {tab === "personalization" && <PersonalizationTab />}
              {tab === "data" && <DataControlsTab />}
              {tab === "security" && <SecurityTab />}
              {tab === "updates" && <UpdatesTab />}
              {tab === "account" && <AccountTab />}
              {tab === "subscription" && <SubscriptionTab />}
            </AnimatePresence>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
