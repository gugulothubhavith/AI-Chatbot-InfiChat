import { Link, useRouterState } from "@tanstack/react-router";
import { MessageSquare, Code2, Database, Image as ImageIcon, Search, Plus, CreditCard, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { UserMenu } from "./UserMenu";
import { HistoryTabs } from "./HistoryTabs";
import { motion } from "framer-motion";
import { tapProps } from "@/lib/motion";
import { usePaletteStore } from "@/stores/palette";
import { useChatStore } from "@/stores/chat";
import { useCodeStore } from "@/stores/code";
import { LogoMark } from "@/components/brand/Logo";
import { useEffect } from "react";

const nav = [
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/code", label: "Code Agent", icon: Code2 },
  { to: "/rag", label: "RAG", icon: Database },
  { to: "/image", label: "Image Gen", icon: ImageIcon },
  { to: "/billing", label: "Billing", icon: CreditCard },
] as const;

export function Sidebar({ open = true, onToggle }: { open?: boolean; onToggle?: () => void }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const openPalette = usePaletteStore((s) => s.setOpen);
  const newChat = useChatStore((s) => s.newChat);
  const newSession = useCodeStore((s) => s.newSession);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        openPalette(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [openPalette]);

  const isCodePage = pathname.startsWith("/code");

  return (
    <motion.aside
      animate={{ width: open ? 288 : 60 }}
      transition={{ type: "spring", stiffness: 260, damping: 30 }}
      className="flex h-screen shrink-0 flex-col overflow-hidden border-r border-border bg-sidebar/70 backdrop-blur-xl"
    >
      {open ? (
        <>
          <div className="flex h-14 items-center justify-between px-3">
            <div className="flex h-9 w-9 items-center justify-center">
              <LogoMark size={17.3} />
            </div>
            <div className="flex items-center gap-1">
              <motion.button
                {...tapProps}
                onClick={() => openPalette(true)}
                aria-label="Search"
                className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-sidebar-accent hover:text-foreground"
              >
                <Search className="h-4 w-4" />
              </motion.button>
              <motion.button
                {...tapProps}
                onClick={onToggle}
                aria-label="Collapse sidebar"
                className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-sidebar-accent hover:text-foreground"
              >
                <PanelLeftClose className="h-4 w-4" />
              </motion.button>
            </div>
          </div>

          <div className="px-3 pb-2">
            <motion.button
              {...tapProps}
              onClick={() => (isCodePage ? newSession() : newChat())}
              className="flex h-9 w-full items-center justify-center gap-1.5 rounded-lg bg-primary text-xs font-medium text-primary-foreground elevated"
            >
              <Plus className="h-3.5 w-3.5" />
              New {isCodePage ? "session" : "chat"}
            </motion.button>
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto settings-scroll">
            <nav className="px-2 py-2">
              {nav.map((item) => {
                const active = pathname === item.to || pathname.startsWith(item.to + "/");
                return (
                  <Link
                    key={item.to}
                    to={item.to}
                    className={`group flex h-8 items-center gap-2.5 rounded-md px-2 text-[13px] transition-colors ${active
                        ? "bg-sidebar-accent text-sidebar-accent-foreground"
                        : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground"
                      }`}
                  >
                    <item.icon className="h-3.5 w-3.5" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            <div className="mt-2">
              <HistoryTabs />
            </div>
          </div>


          <div className="border-t border-border p-2">
            <UserMenu />
            <div className="mt-2 flex items-center gap-1.5 px-2 text-[11px] text-muted-foreground">
              <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              All systems normal
            </div>
          </div>
        </>

      ) : (
        <div className="flex h-full w-[60px] flex-col items-center">
          <div className="flex h-14 items-center justify-center">
            <motion.button
              {...tapProps}
              onClick={onToggle}
              aria-label="Open sidebar"
              className="group relative flex h-9 w-9 items-center justify-center rounded-md text-foreground hover:bg-sidebar-accent"
            >
              <LogoMark size={17.3} className="transition-opacity duration-150 group-hover:opacity-0" />
              <PanelLeftOpen className="absolute h-4 w-4 opacity-0 transition-opacity duration-150 group-hover:opacity-100" />
            </motion.button>
          </div>

          <div className="mt-2 h-px w-8 bg-border" />

          <motion.button
            {...tapProps}
            onClick={() => openPalette(true)}
            aria-label="Search"
            className="mt-2 flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-sidebar-accent hover:text-foreground"
          >
            <Search className="h-4 w-4" />
          </motion.button>

          <motion.button
            {...tapProps}
            onClick={() => (isCodePage ? newSession() : newChat())}
            aria-label="New chat"
            className="mt-2 flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground elevated"
          >
            <Plus className="h-4 w-4" />
          </motion.button>

          <div className="mt-3 flex flex-col items-center gap-1">
            {nav.map((item) => {
              const active = pathname === item.to || pathname.startsWith(item.to + "/");
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  aria-label={item.label}
                  className={`flex h-8 w-8 items-center justify-center rounded-md transition-colors ${active
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-foreground"
                    }`}
                >
                  <item.icon className="h-4 w-4" />
                </Link>
              );
            })}
          </div>

          <div className="mt-auto">
            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          </div>
        </div>
      )}
    </motion.aside>
  );
}
