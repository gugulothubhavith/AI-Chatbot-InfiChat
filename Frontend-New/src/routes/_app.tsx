import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { Sidebar } from "@/components/shell/Sidebar";
import { CommandPalette } from "@/components/shell/CommandPalette";
import { SettingsDialog } from "@/components/shell/SettingsDialog";
import { useAuthStore } from "@/stores/auth";
import { useState, useEffect } from "react";
import { SettingsContext } from "@/components/shell/settings-context";
import { useChatStore } from "@/stores/chat";

export const Route = createFileRoute("/_app")({
  beforeLoad: () => {
    if (typeof window !== "undefined") {
      const raw = window.localStorage.getItem("infichat-auth");
      try {
        const parsed = raw ? JSON.parse(raw) : null;
        if (!parsed?.state?.user || !parsed?.state?.token) {
          throw redirect({ to: "/login" });
        }
      } catch (e) {
        if (e && typeof e === "object" && "to" in e) throw e;
        // No valid auth data — redirect
        throw redirect({ to: "/login" });
      }
    }
    return {};
  },
  component: AppLayout,
});

function AppLayout() {
  const { hydrate } = useAuthStore();
  const loadSessions = useChatStore((s) => s.loadSessions);
  useEffect(() => {
    hydrate();
    loadSessions();
  }, [hydrate, loadSessions]);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  return (
    <SettingsContext.Provider value={{ open: settingsOpen, setOpen: setSettingsOpen }}>
      <div className="flex h-screen w-full overflow-hidden bg-background">
        <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen((v) => !v)} />
        <main className="flex-1 min-w-0 relative">
          <Outlet />
        </main>
        <CommandPalette />
        <SettingsDialog open={settingsOpen} onOpenChange={setSettingsOpen} />
      </div>
    </SettingsContext.Provider>
  );
}
