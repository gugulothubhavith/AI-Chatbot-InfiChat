import { useRef, useState } from "react";
import { Block, Row, SectionTitle, TabShell } from "./_primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";
import { Camera, Info } from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { toast } from "sonner";

export function AccountTab() {
  const user = useAuthStore((s) => s.user);
  const updateProfile = useAuthStore((s) => s.updateProfile);
  const signOut = useAuthStore((s) => s.signOut);
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const readFile = (f: File) => {
    const r = new FileReader();
    r.onload = () => { updateProfile({ avatar: String(r.result) }); toast.success("Avatar updated"); };
    r.readAsDataURL(f);
  };

  return (
    <TabShell keyId="account">
      <SectionTitle title="Profile" description="How you appear across InfiChat." />
      <div className="mb-6 flex items-center gap-5">
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files?.[0]; if (f) readFile(f); }}
          onClick={() => inputRef.current?.click()}
          className={`group relative flex h-20 w-20 cursor-pointer items-center justify-center overflow-hidden rounded-full border-2 border-dashed transition-colors ${
            dragOver ? "border-brand bg-brand/10" : "border-border bg-surface/40"
          }`}
        >
          {user?.avatar ? (
            <img src={user.avatar} alt="" referrerPolicy="no-referrer" className="h-full w-full object-cover" />
          ) : (
            <span className="text-lg font-semibold text-muted-foreground">{user?.name.slice(0, 1) ?? "U"}</span>
          )}
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100">
            <Camera className="h-5 w-5 text-white" />
          </div>
          <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) readFile(f); }} />
        </div>
        <div className="text-xs text-muted-foreground">
          <div className="text-[13px] font-medium text-foreground">Drag or click to upload</div>
          PNG or JPG, max 5MB. Square images work best.
        </div>
      </div>

      <Block>
        <Row title="Display name" description="Shown in shared chats and mentions.">
          <Input
            value={user?.name ?? ""}
            onChange={(e) => updateProfile({ name: e.target.value })}
            onBlur={() => toast("Display name saved")}
            className="h-8 w-[220px] bg-surface/40 text-xs"
          />
        </Row>
        <Row title="Email address" description="Used for sign in and receipts.">
          <div className="flex items-center gap-1.5">
            <Input disabled value={user?.email ?? ""} className="h-8 w-[220px] bg-surface/40 text-xs opacity-70" />
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button className="text-muted-foreground"><Info className="h-3.5 w-3.5" /></button>
                </TooltipTrigger>
                <TooltipContent side="left">Contact support to change your email.</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        </Row>
      </Block>

      <div className="h-6" />
      <SectionTitle title="Danger zone" />
      <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-[13px] font-medium text-destructive">Delete account</div>
            <div className="mt-0.5 text-xs text-muted-foreground">Permanently removes your account, chats, and data.</div>
          </div>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button size="sm" variant="destructive">Delete account</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete your account?</AlertDialogTitle>
                <AlertDialogDescription>This permanently removes your account and every conversation associated with it. This action cannot be undone.</AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={() => { signOut(); toast.error("Account deleted"); }} className="bg-destructive hover:bg-destructive/90">Delete account</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
    </TabShell>
  );
}
