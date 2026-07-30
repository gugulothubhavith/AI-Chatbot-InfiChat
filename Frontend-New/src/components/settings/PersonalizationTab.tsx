import { useSettingsStore } from "@/stores/settings";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Block, Row, SectionTitle, TabShell } from "./_primitives";
import { toast } from "sonner";
import { useRef } from "react";

function useDebouncedToast() {
  const t = useRef<number | null>(null);
  return (label: string) => {
    if (t.current) window.clearTimeout(t.current);
    t.current = window.setTimeout(() => toast(label), 400);
  };
}

export function PersonalizationTab() {
  const s = useSettingsStore();
  const debouncedToast = useDebouncedToast();

  return (
    <TabShell keyId="personalization">
      <SectionTitle title="Custom instructions" description="Tell InfiChat how you'd like it to respond." />
      <Textarea
        value={s.customInstructions}
        onChange={(e) => { s.set("customInstructions", e.target.value); debouncedToast("Custom instructions saved"); }}
        placeholder="Additional behavior, style, and tone preferences"
        className="mb-6 min-h-[110px] resize-none bg-surface/40 text-[13px]"
      />

      <SectionTitle title="About you" description="Small facts help InfiChat feel personal." />
      <div className="mb-6 grid grid-cols-2 gap-3">
        <div className="col-span-1 rounded-xl border border-border/70 bg-surface/40 p-3">
          <div className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Nickname</div>
          <Input value={s.nickname} onChange={(e) => { s.set("nickname", e.target.value); debouncedToast("Nickname saved"); }} className="h-8 border-0 bg-transparent px-0 text-[13px] focus-visible:ring-0" />
        </div>
        <div className="col-span-1 rounded-xl border border-border/70 bg-surface/40 p-3">
          <div className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Occupation</div>
          <Input value={s.occupation} onChange={(e) => { s.set("occupation", e.target.value); debouncedToast("Occupation saved"); }} className="h-8 border-0 bg-transparent px-0 text-[13px] focus-visible:ring-0" />
        </div>
        <div className="col-span-2 rounded-xl border border-border/70 bg-surface/40 p-3">
          <div className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Interests & context</div>
          <Textarea value={s.interests} onChange={(e) => { s.set("interests", e.target.value); debouncedToast("Interests saved"); }} className="min-h-[70px] resize-none border-0 bg-transparent p-0 text-[13px] focus-visible:ring-0" />
        </div>
      </div>

      <SectionTitle title="Memory & context" />
      <Block>
        <Row title="Personalize responses" description="Use my nickname and context in replies.">
          <Switch checked={s.personalizeResponses} onCheckedChange={(v) => { s.set("personalizeResponses", v); toast(v ? "Personalization on" : "Personalization off"); }} />
        </Row>
        <Row title="Conversation memory" description="Remember facts from previous conversations.">
          <Switch checked={s.conversationMemory} onCheckedChange={(v) => { s.set("conversationMemory", v); toast(v ? "Memory on" : "Memory off"); }} />
        </Row>
      </Block>

      <div className="h-6" />
      <SectionTitle title="Advanced" />
      <Block>
        <Row title="Python code interpreter" description="Execute code in an isolated container.">
          <Switch checked={s.pythonInterpreter} onCheckedChange={(v) => { s.set("pythonInterpreter", v); toast(v ? "Interpreter enabled" : "Interpreter disabled"); }} />
        </Row>
        <Row title="InfiChat Voice" description="Enable spoken responses.">
          <Switch checked={s.voiceTTS} onCheckedChange={(v) => { s.set("voiceTTS", v); toast(v ? "Voice enabled" : "Voice disabled"); }} />
        </Row>
      </Block>
    </TabShell>
  );
}
