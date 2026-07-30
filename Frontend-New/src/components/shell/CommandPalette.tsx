import { CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { usePaletteStore } from "@/stores/palette";
import { useChatStore } from "@/stores/chat";
import { useCodeStore } from "@/stores/code";
import { MODELS, useModelStore } from "@/stores/model";
import { useSettingsStore } from "@/stores/settings";
import { useNavigate } from "@tanstack/react-router";
import { MessageSquare, Code2, Sparkles, Sun, Moon, Monitor } from "lucide-react";

export function CommandPalette() {
  const open = usePaletteStore((s) => s.open);
  const setOpen = usePaletteStore((s) => s.setOpen);
  const chats = useChatStore((s) => s.conversations);
  const setActiveChat = useChatStore((s) => s.setActive);
  const sessions = useCodeStore((s) => s.sessions);
  const setActiveCode = useCodeStore((s) => s.setActive);
  const setModel = useModelStore((s) => s.setModel);
  const setSetting = useSettingsStore((s) => s.set);
  const setTheme = (t: "light" | "dark" | "system") => setSetting("theme", t);
  const nav = useNavigate();

  const close = () => setOpen(false);
  const go = (fn: () => void) => {
    fn();
    close();
  };

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Search chats, models, actions…" />
      <CommandList>
        <CommandEmpty>No results.</CommandEmpty>
        <CommandGroup heading="Chats">
          {chats.slice(0, 6).map((c) => (
            <CommandItem key={c.id} onSelect={() => go(() => { setActiveChat(c.id); nav({ to: "/chat" }); })}>
              <MessageSquare className="mr-2 !h-3.5 !w-3.5" />
              <span className="truncate">{c.title}</span>
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandGroup heading="Code Sessions">
          {sessions.slice(0, 4).map((c) => (
            <CommandItem key={c.id} onSelect={() => go(() => { setActiveCode(c.id); nav({ to: "/code" }); })}>
              <Code2 className="mr-2 !h-3.5 !w-3.5" />
              <span className="truncate">{c.title}</span>
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandGroup heading="Switch Model">
          {MODELS.map((m) => (
            <CommandItem key={m.id} onSelect={() => go(() => setModel(m.id))}>
              <Sparkles className="mr-2 !h-3.5 !w-3.5" />
              <span>{m.name}</span>
              <span className="ml-auto text-[11px] text-muted-foreground">{m.provider}</span>
            </CommandItem>
          ))}
        </CommandGroup>
        <CommandGroup heading="Theme">
          <CommandItem onSelect={() => go(() => setTheme("light"))}>
            <Sun className="mr-2 !h-3.5 !w-3.5" /> Light
          </CommandItem>
          <CommandItem onSelect={() => go(() => setTheme("dark"))}>
            <Moon className="mr-2 !h-3.5 !w-3.5" /> Dark
          </CommandItem>
          <CommandItem onSelect={() => go(() => setTheme("system"))}>
            <Monitor className="mr-2 !h-3.5 !w-3.5" /> System
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
