import { useState, useEffect } from "react";
import { Block, Row, SectionTitle, TabShell } from "./_primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Eye, EyeOff, Copy, Plus, Trash2 } from "lucide-react";
import { useSettingsStore } from "@/stores/settings";
import { toast } from "sonner";
import { api } from "@/lib/api";

type Key = { id: string; name: string; prefix: string; token?: string; created_at: string; scopes: string[] };

export function SecurityTab() {
  const piiScrubbing = useSettingsStore((s) => s.piiScrubbing);
  const setSetting = useSettingsStore((s) => s.set);
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [keys, setKeys] = useState<Key[]>([]);
  const [loading, setLoading] = useState(true);
  const [revealed, setRevealed] = useState<Record<string, boolean>>({});

  useEffect(() => {
    api.getApiKeys().then(data => {
      setKeys(data as Key[]);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const changePw = () => {
    if (!current || !next || next !== confirm) {
      toast.error("Passwords don't match");
      return;
    }
    setCurrent(""); setNext(""); setConfirm("");
    toast.success("Password updated");
  };

  const createKey = async () => {
    try {
      const res = await api.createApiKey("New token", ["full_access"]);
      setKeys((p) => [res as Key, ...p]);
      toast.success("Personal access token created");
    } catch (e) {
      toast.error("Failed to create token");
    }
  };

  const deleteKey = async (id: string) => {
    try {
      await api.deleteApiKey(id);
      setKeys((p) => p.filter(k => k.id !== id));
      toast.success("Token deleted");
    } catch (e) {
      toast.error("Failed to delete token");
    }
  };

  return (
    <TabShell keyId="security">
      <SectionTitle title="Change password" description="Rotate your password regularly." />
      <div className="mb-6 space-y-2.5">
        <Input type="password" placeholder="Current password" value={current} onChange={(e) => setCurrent(e.target.value)} className="h-9 bg-surface/40" />
        <Input type="password" placeholder="New password" value={next} onChange={(e) => setNext(e.target.value)} className="h-9 bg-surface/40" />
        <Input type="password" placeholder="Confirm new password" value={confirm} onChange={(e) => setConfirm(e.target.value)} className="h-9 bg-surface/40" />
        <div className="flex justify-end">
          <Button size="sm" onClick={changePw}>Update password</Button>
        </div>
      </div>

      <SectionTitle title="Personal access tokens" description="Generate tokens to use the InfiChat API. Tokens with specific scopes provide granular access." />
      <div className="mb-6 divide-y divide-border/60 rounded-xl border border-border/70 bg-surface/40">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="text-xs text-muted-foreground">{loading ? "Loading..." : `${keys.length} active token${keys.length === 1 ? "" : "s"}`}</div>
          <Button size="sm" variant="outline" onClick={createKey}><Plus className="mr-1.5 h-3.5 w-3.5" />New token</Button>
        </div>
        {keys.map((k) => (
          <div key={k.id} className="flex flex-col gap-1 px-4 py-3">
            <div className="flex items-center justify-between gap-3">
            <div className="min-w-0 flex-1">
              <div className="text-[13px] font-medium">{k.name}</div>
              <div className="mt-0.5 flex items-center gap-2">
                <code className="truncate rounded bg-surface-2 px-1.5 py-0.5 font-mono text-[11px] text-muted-foreground">
                  {k.token ? (revealed[k.id] ? k.token : "•".repeat(k.token.length)) : k.prefix}
                </code>
                {k.token && (
                  <>
                    <button onClick={() => setRevealed((r) => ({ ...r, [k.id]: !r[k.id] }))} className="text-muted-foreground hover:text-foreground" aria-label="Toggle reveal">
                      {revealed[k.id] ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                    </button>
                    <button onClick={() => { navigator.clipboard.writeText(k.token!); toast("Token copied"); }} className="text-muted-foreground hover:text-foreground" aria-label="Copy">
                      <Copy className="h-3.5 w-3.5" />
                    </button>
                  </>
                )}
              </div>
              <div className="mt-1 flex items-center gap-2 text-[11px] text-muted-foreground">
                <span>Created {new Date(k.created_at).toLocaleDateString()}</span>
                {k.scopes && k.scopes.length > 0 && (
                  <span className="rounded bg-primary/10 px-1 py-0.5 text-primary">{k.scopes.join(", ")}</span>
                )}
              </div>
            </div>
            <button onClick={() => deleteKey(k.id)} className="text-muted-foreground hover:text-destructive">
              <Trash2 className="h-3.5 w-3.5" />
            </button>
            </div>
          </div>
        ))}
      </div>

      <SectionTitle title="Privacy" />
      <Block>
        <Row title="Privacy mode (PII scrubbing)" description="Automatically redacts emails and phone numbers from logs.">
          <Switch checked={piiScrubbing} onCheckedChange={(v) => { setSetting("piiScrubbing", v); toast(v ? "PII scrubbing enabled" : "PII scrubbing disabled"); }} />
        </Row>
      </Block>
    </TabShell>
  );
}
