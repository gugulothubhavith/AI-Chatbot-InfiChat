import { useSettingsStore, type NotifKey } from "@/stores/settings";
import { Block, Row, SectionTitle, TabShell } from "./_primitives";
import { Bell, Mail } from "lucide-react";
import { toast } from "sonner";
import { motion } from "framer-motion";

const items: { id: NotifKey; title: string; description: string }[] = [
  { id: "responses", title: "Responses", description: "Get notified when InfiChat finishes a response that takes time." },
  { id: "recommendations", title: "Recommendations", description: "Stay in the loop on new tools, tips, and features." },
  { id: "usage", title: "Usage", description: "We'll notify you when usage limits reset." },
];

function Chip({ active, onClick, icon: Icon, label }: { active: boolean; onClick: () => void; icon: React.ComponentType<{ className?: string }>; label: string }) {
  return (
    <motion.button
      whileTap={{ scale: 0.96 }}
      onClick={onClick}
      className={`flex h-7 items-center gap-1.5 rounded-full border px-2.5 text-[11px] font-medium transition-colors ${
        active
          ? "border-brand/40 bg-brand/15 text-foreground"
          : "border-border bg-surface/40 text-muted-foreground hover:text-foreground"
      }`}
    >
      <Icon className={`h-3 w-3 ${active ? "text-brand" : ""}`} />
      {label}
    </motion.button>
  );
}

export function NotificationsTab() {
  const notifications = useSettingsStore((s) => s.notifications);
  const setNotif = useSettingsStore((s) => s.setNotif);

  return (
    <TabShell keyId="notifications">
      <SectionTitle title="Notifications" description="Choose how you want to be reached for each event type." />
      <Block>
        {items.map((it) => {
          const state = notifications[it.id];
          return (
            <Row key={it.id} title={it.title} description={it.description}>
              <div className="flex items-center gap-1.5">
                <Chip
                  active={state.push}
                  onClick={() => { setNotif(it.id, "push", !state.push); toast(`Push ${!state.push ? "on" : "off"} · ${it.title}`); }}
                  icon={Bell}
                  label="Push"
                />
                <Chip
                  active={state.email}
                  onClick={() => { setNotif(it.id, "email", !state.email); toast(`Email ${!state.email ? "on" : "off"} · ${it.title}`); }}
                  icon={Mail}
                  label="Email"
                />
              </div>
            </Row>
          );
        })}
      </Block>
    </TabShell>
  );
}
