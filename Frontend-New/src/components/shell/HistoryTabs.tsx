import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useChatStore } from "@/stores/chat";
import { useCodeStore } from "@/stores/code";
import { Pencil, Trash2, Check, X } from "lucide-react";
import { useState } from "react";
import { useNavigate, useRouterState } from "@tanstack/react-router";
import { motion, AnimatePresence } from "framer-motion";

type Item = { id: string; title: string; createdAt: number };

function groupByDay(items: Item[]): { label: string; items: Item[] }[] {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const yesterday = today.getTime() - 86400000;
  const week = today.getTime() - 7 * 86400000;
  const groups = { Today: [] as Item[], Yesterday: [] as Item[], "Previous 7 Days": [] as Item[], Older: [] as Item[] };
  for (const it of items) {
    if (it.createdAt >= today.getTime()) groups.Today.push(it);
    else if (it.createdAt >= yesterday) groups.Yesterday.push(it);
    else if (it.createdAt >= week) groups["Previous 7 Days"].push(it);
    else groups.Older.push(it);
  }
  return Object.entries(groups)
    .filter(([, arr]) => arr.length > 0)
    .map(([label, items]) => ({ label, items }));
}

export function HistoryTabs() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const defaultTab = pathname.startsWith("/code") ? "code" : "chat";

  return (
    <Tabs defaultValue={defaultTab} className="flex h-full flex-col">
      <TabsList className="mx-3 grid grid-cols-2 bg-surface-2/50">
        <TabsTrigger value="chat" className="text-xs">Chat History</TabsTrigger>
        <TabsTrigger value="code" className="text-xs">Code History</TabsTrigger>
      </TabsList>
      <TabsContent value="chat" className="mt-2 flex-1 min-h-0 overflow-hidden">
        <ChatHistoryList />
      </TabsContent>
      <TabsContent value="code" className="mt-2 flex-1 min-h-0 overflow-hidden">
        <CodeHistoryList />
      </TabsContent>
    </Tabs>
  );
}

function ChatHistoryList() {
  const conversations = useChatStore((s) => s.conversations);
  const activeId = useChatStore((s) => s.activeId);
  const setActive = useChatStore((s) => s.setActive);
  const rename = useChatStore((s) => s.rename);
  const remove = useChatStore((s) => s.remove);
  const nav = useNavigate();
  const groups = groupByDay(conversations);

  return (
    <HistoryList
      groups={groups}
      activeId={activeId}
      onSelect={(id) => {
        setActive(id);
        nav({ to: "/chat" });
      }}
      onRename={rename}
      onDelete={remove}
    />
  );
}

function CodeHistoryList() {
  const sessions = useCodeStore((s) => s.sessions);
  const activeId = useCodeStore((s) => s.activeId);
  const setActive = useCodeStore((s) => s.setActive);
  const rename = useCodeStore((s) => s.rename);
  const remove = useCodeStore((s) => s.remove);
  const nav = useNavigate();
  const groups = groupByDay(sessions);
  return (
    <HistoryList
      groups={groups}
      activeId={activeId}
      onSelect={(id) => {
        setActive(id);
        nav({ to: "/code" });
      }}
      onRename={rename}
      onDelete={remove}
    />
  );
}

function HistoryList({
  groups,
  activeId,
  onSelect,
  onRename,
  onDelete,
}: {
  groups: { label: string; items: Item[] }[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onRename: (id: string, title: string) => void;
  onDelete: (id: string) => void;
}) {
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  return (
    <ScrollArea className="h-full">
      <div className="space-y-4 px-2 pb-4">
        {groups.map((g) => (
          <div key={g.label}>
            <div className="px-2 pb-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              {g.label}
            </div>
            <div className="space-y-0.5">
              <AnimatePresence initial={false}>
                {g.items.map((it) => {
                  const active = it.id === activeId;
                  const isEditing = editing === it.id;
                  return (
                    <motion.div
                      key={it.id}
                      layout
                      initial={{ opacity: 0, y: -4 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -8 }}
                      className={`group relative flex min-w-0 h-8 items-center gap-1 rounded-md pl-2 pr-1 text-[13px] ${
                        active ? "bg-sidebar-accent text-foreground" : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground"
                      }`}
                    >
                      {isEditing ? (
                        <>
                          <input
                            autoFocus
                            value={draft}
                            onChange={(e) => setDraft(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                onRename(it.id, draft.trim() || it.title);
                                setEditing(null);
                              } else if (e.key === "Escape") setEditing(null);
                            }}
                            className="h-6 flex-1 min-w-0 rounded border border-border bg-background px-1 text-[12px] outline-none focus:border-brand"
                          />
                          <button className="shrink-0 p-1" onClick={() => { onRename(it.id, draft.trim() || it.title); setEditing(null); }}>
                            <Check className="h-3 w-3" />
                          </button>
                          <button className="shrink-0 p-1" onClick={() => setEditing(null)}>
                            <X className="h-3 w-3" />
                          </button>
                        </>
                      ) : (
                        <>
                          <button className="flex-1 min-w-0 truncate text-left pr-2" onClick={() => onSelect(it.id)}>
                            {it.title}
                          </button>
                          <div className="flex shrink-0 gap-0.5 text-muted-foreground/90">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setEditing(it.id);
                                setDraft(it.title);
                              }}
                              className="rounded p-1 hover:bg-surface"
                            >
                              <Pencil className="h-3 w-3" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                onDelete(it.id);
                              }}
                              className="rounded p-1 hover:bg-destructive/10 hover:text-destructive"
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          </div>
                        </>
                      )}
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
