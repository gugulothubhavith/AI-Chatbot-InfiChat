import { useSettingsStore, ACCENTS, type AccentKey, type AppLang, type SpokenLang, type VoiceProfile } from "@/stores/settings";
import { useModelStore } from "@/stores/model";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Sun, Moon, Monitor, Play, Loader2, Check, Plus, Trash2, KeyRound } from "lucide-react";
import { Block, Row, SectionTitle, TabShell } from "./_primitives";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { useState } from "react";

const themes = [
  { id: "light", label: "Light", icon: Sun },
  { id: "dark", label: "Dark", icon: Moon },
  { id: "system", label: "System", icon: Monitor },
] as const;

const voices: { id: VoiceProfile; label: string; sub: string }[] = [
  { id: "pro-en-male", label: "Professional English", sub: "Male" },
  { id: "corp-hi-female", label: "Corporate Hindi", sub: "Female" },
  { id: "empathetic-te-male", label: "Empathetic Telugu", sub: "Male" },
  { id: "alert-hi-fast", label: "Alert Hindi", sub: "Fast" },
];

export function GeneralTab() {
  const s = useSettingsStore();
  const [previewing, setPreviewing] = useState(false);

  const preview = () => {
    setPreviewing(true);
    setTimeout(() => {
      setPreviewing(false);
      toast("Voice preview played", { description: voices.find((v) => v.id === s.voiceProfile)?.label });
    }, 900);
  };

  return (
    <TabShell keyId="general">
      <SectionTitle title="Appearance" description="Customize how InfiChat looks on this device." />
      <div className="mb-6 grid grid-cols-3 gap-3">
        {themes.map((t) => {
          const active = s.theme === t.id;
          return (
            <motion.button
              key={t.id}
              whileTap={{ scale: 0.97 }}
              onClick={() => { s.set("theme", t.id); toast("Theme updated", { description: t.label }); }}
              className={`group relative flex flex-col items-center gap-2 rounded-xl border p-4 transition-all ${
                active ? "border-brand ring-2 ring-brand/40 bg-brand/5" : "border-border hover:border-border/80 bg-surface/40"
              }`}
            >
              <div className={`flex h-14 w-full items-center justify-center rounded-lg ${
                t.id === "light" ? "bg-white" : t.id === "dark" ? "bg-neutral-900" : "bg-gradient-to-br from-white to-neutral-900"
              }`}>
                <t.icon className={`h-5 w-5 ${t.id === "light" ? "text-neutral-800" : "text-neutral-200"}`} />
              </div>
              <div className="text-[12px] font-medium">{t.label}</div>
              {active && <Check className="absolute right-2 top-2 h-3.5 w-3.5 text-brand" />}
            </motion.button>
          );
        })}
      </div>

      <SectionTitle title="Accent color" description="Used throughout the interface." />
      <div className="mb-6 flex items-center gap-2.5">
        {(Object.keys(ACCENTS) as AccentKey[]).map((k) => {
          const a = ACCENTS[k];
          const active = s.accent === k;
          return (
            <button
              key={k}
              onClick={() => { s.set("accent", k); toast("Accent updated", { description: a.label }); }}
              aria-label={a.label}
              className={`relative h-8 w-8 rounded-full transition-transform hover:scale-110 ${
                active ? "ring-2 ring-offset-2 ring-offset-background" : ""
              }`}
              style={{ backgroundColor: a.swatch, boxShadow: active ? `0 0 0 2px ${a.swatch}` : undefined }}
            >
              {active && <Check className="absolute inset-0 m-auto h-4 w-4 text-white" />}
            </button>
          );
        })}
      </div>

      <SectionTitle title="Language" />
      <Block>
        <Row title="App language" description="Interface language across the app.">
          <Select value={s.appLang} onValueChange={(v) => { s.set("appLang", v as AppLang); toast("App language updated"); }}>
            <SelectTrigger className="h-8 w-[180px] text-xs"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="auto">Auto detect</SelectItem>
              <SelectItem value="en">English</SelectItem>
              <SelectItem value="hi">Hindi</SelectItem>
              <SelectItem value="ja">Japanese</SelectItem>
            </SelectContent>
          </Select>
        </Row>
        <Row title="Spoken language" description="Used for voice conversations.">
          <Select value={s.spokenLang} onValueChange={(v) => { s.set("spokenLang", v as SpokenLang); toast("Spoken language updated"); }}>
            <SelectTrigger className="h-8 w-[180px] text-xs"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="auto">Auto detect</SelectItem>
              <SelectItem value="en">English</SelectItem>
              <SelectItem value="hi">Hindi</SelectItem>
            </SelectContent>
          </Select>
        </Row>
      </Block>

      <div className="h-6" />
      <SectionTitle title="Voice" description="Configure the InfiChat voice engine." />
      <Block>
        <Row title="Voice profile" description="Timbre and delivery style.">
          <div className="flex items-center gap-2">
            <Select value={s.voiceProfile} onValueChange={(v) => { s.set("voiceProfile", v as VoiceProfile); toast("Voice profile updated"); }}>
              <SelectTrigger className="h-8 w-[220px] text-xs"><SelectValue /></SelectTrigger>
              <SelectContent>
                {voices.map((v) => (
                  <SelectItem key={v.id} value={v.id}>
                    <span className="font-medium">{v.label}</span>
                    <span className="ml-1.5 text-muted-foreground">· {v.sub}</span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <button
              onClick={preview}
              className="flex h-8 w-8 items-center justify-center rounded-md border border-border bg-surface hover:bg-surface-2"
              aria-label="Play preview"
            >
              {previewing ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
            </button>
          </div>
        </Row>
        <Row title="Separate voice window" description="Keep InfiChat voice in a separate full-screen surface.">
          <Switch checked={s.voiceFullscreen} onCheckedChange={(v) => { s.set("voiceFullscreen", v); toast(v ? "Separate voice window enabled" : "Separate voice window disabled"); }} />
        </Row>
      </Block>

      <div className="h-6" />
      <CustomModelsSection />
    </TabShell>
  );
}

function CustomModelsSection() {
  const customModels = useModelStore((s) => s.customModels);
  const addCustomModel = useModelStore((s) => s.addCustomModel);
  const removeCustomModel = useModelStore((s) => s.removeCustomModel);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", provider: "", endpoint: "", apiKey: "", desc: "" });

  const submit = () => {
    if (!form.name.trim() || !form.endpoint.trim()) {
      toast.error("Name and endpoint are required");
      return;
    }
    const entry = addCustomModel(form);
    toast.success("Custom model added", { description: entry.name });
    setForm({ name: "", provider: "", endpoint: "", apiKey: "", desc: "" });
    setOpen(false);
  };

  return (
    <>
      <SectionTitle
        title="Custom models"
        description="Connect your own model endpoint — OpenAI-compatible, local Ollama, or a private gateway."
      />
      <Block>
        {customModels.length === 0 && !open && (
          <div className="flex items-center justify-between px-3 py-3">
            <div className="text-[12px] text-muted-foreground">
              No custom models yet. Bring your own endpoint and API key.
            </div>
            <button
              onClick={() => setOpen(true)}
              className="inline-flex h-8 items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 text-[12px] font-medium hover:bg-surface-2"
            >
              <Plus className="h-3.5 w-3.5" /> Add model
            </button>
          </div>
        )}

        {customModels.map((m) => (
          <div
            key={m.id}
            className="flex items-center justify-between gap-3 border-b border-border/60 px-3 py-2.5 last:border-b-0"
          >
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-medium">{m.name}</span>
                <span className="rounded-full bg-brand/10 px-1.5 py-0.5 text-[10px] font-medium text-brand">
                  {m.provider}
                </span>
              </div>
              <div className="mt-0.5 truncate font-mono text-[11px] text-muted-foreground">
                {m.endpoint}
              </div>
              {m.apiKeyMasked && (
                <div className="mt-0.5 flex items-center gap-1 text-[10px] text-muted-foreground">
                  <KeyRound className="h-3 w-3" />
                  {m.apiKeyMasked}
                </div>
              )}
            </div>
            <button
              onClick={() => {
                removeCustomModel(m.id);
                toast("Removed", { description: m.name });
              }}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-muted-foreground hover:bg-surface-2 hover:text-destructive"
              aria-label="Remove model"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}

        <AnimatePresence initial={false}>
          {open && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden border-t border-border/60"
            >
              <div className="grid grid-cols-2 gap-3 p-3">
                <label className="col-span-1 text-[11px] font-medium text-muted-foreground">
                  Display name
                  <Input
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="My GPT-4 Turbo"
                    className="mt-1 h-8 text-xs"
                  />
                </label>
                <label className="col-span-1 text-[11px] font-medium text-muted-foreground">
                  Provider label
                  <Input
                    value={form.provider}
                    onChange={(e) => setForm({ ...form, provider: e.target.value })}
                    placeholder="OpenAI / Azure / Custom"
                    className="mt-1 h-8 text-xs"
                  />
                </label>
                <label className="col-span-2 text-[11px] font-medium text-muted-foreground">
                  Endpoint URL
                  <Input
                    value={form.endpoint}
                    onChange={(e) => setForm({ ...form, endpoint: e.target.value })}
                    placeholder="https://api.example.com/v1/chat/completions"
                    className="mt-1 h-8 font-mono text-xs"
                  />
                </label>
                <label className="col-span-2 text-[11px] font-medium text-muted-foreground">
                  API key
                  <Input
                    type="password"
                    value={form.apiKey}
                    onChange={(e) => setForm({ ...form, apiKey: e.target.value })}
                    placeholder="sk-..."
                    className="mt-1 h-8 font-mono text-xs"
                  />
                  <span className="mt-1 block text-[10px] font-normal text-muted-foreground">
                    Stored locally in this browser only. Never sent anywhere else.
                  </span>
                </label>
                <label className="col-span-2 text-[11px] font-medium text-muted-foreground">
                  Description (optional)
                  <Input
                    value={form.desc}
                    onChange={(e) => setForm({ ...form, desc: e.target.value })}
                    placeholder="Notes about this model"
                    className="mt-1 h-8 text-xs"
                  />
                </label>
                <div className="col-span-2 flex justify-end gap-2 pt-1">
                  <button
                    onClick={() => setOpen(false)}
                    className="h-8 rounded-md border border-border bg-surface px-3 text-[12px] hover:bg-surface-2"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={submit}
                    className="h-8 rounded-md bg-brand px-3 text-[12px] font-medium text-white hover:opacity-90"
                  >
                    Save model
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {customModels.length > 0 && !open && (
          <button
            onClick={() => setOpen(true)}
            className="flex w-full items-center justify-center gap-1.5 border-t border-border/60 px-3 py-2.5 text-[12px] font-medium text-muted-foreground hover:bg-surface-2 hover:text-foreground"
          >
            <Plus className="h-3.5 w-3.5" /> Add another model
          </button>
        )}
      </Block>
    </>
  );
}
