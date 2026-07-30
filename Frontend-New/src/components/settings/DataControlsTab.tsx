import { useState } from "react";
import { Block, Row, SectionTitle, TabShell } from "./_primitives";
import { Button } from "@/components/ui/button";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { ChevronRight, ChevronLeft, Upload, Trash2, Download, ExternalLink, FileText } from "lucide-react";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";

type View = "root" | "rag" | "shared" | "archived";

const initialDocs = [
  { id: "d1", name: "product-spec.pdf", size: "2.4 MB" },
  { id: "d2", name: "onboarding.docx", size: "812 KB" },
  { id: "d3", name: "runbook.pdf", size: "1.1 MB" },
];
const initialShared = [
  { id: "s1", title: "Rewrite of the pricing page", when: "2 days ago" },
  { id: "s2", title: "Onboarding email drafts", when: "1 week ago" },
];
const initialArchived = [
  { id: "a1", title: "Q3 planning brainstorm", when: "Jul 12" },
  { id: "a2", title: "API redesign discussion", when: "Jun 30" },
];

export function DataControlsTab() {
  const [view, setView] = useState<View>("root");
  const [docs, setDocs] = useState(initialDocs);
  const [shared, setShared] = useState(initialShared);
  const [archived, setArchived] = useState(initialArchived);

  const exportData = () => toast.success("Data export queued", { description: "You'll receive a download link shortly." });
  const deleteAll = () => toast.error("All chats deleted", { description: "This action cannot be undone." });

  return (
    <TabShell keyId="data">
      <AnimatePresence mode="wait">
        {view === "root" && (
          <motion.div key="root" initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} transition={{ duration: 0.18 }}>
            <SectionTitle title="Data controls" description="Manage what InfiChat stores about you." />
            <Block>
              <ManageRow title="Knowledge base (RAG)" description="Upload files that ground responses." onClick={() => setView("rag")} />
              <ManageRow title="Shared links" description="Public links to chats you've shared." onClick={() => setView("shared")} />
              <ManageRow title="Archived chats" description="Restore or permanently delete chats." onClick={() => setView("archived")} />
              <Row title="Export data" description="Download a JSON archive of your chats and settings.">
                <Button size="sm" variant="outline" onClick={exportData}><Download className="mr-1.5 h-3.5 w-3.5" />Download</Button>
              </Row>
            </Block>

            <div className="h-6" />
            <SectionTitle title="Danger zone" />
            <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-[13px] font-medium text-destructive">Delete all chats</div>
                  <div className="mt-0.5 text-xs text-muted-foreground">Permanently removes every conversation. This cannot be undone.</div>
                </div>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button size="sm" variant="destructive">Delete all</Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Delete every conversation?</AlertDialogTitle>
                      <AlertDialogDescription>This permanently removes all chats from your account. This action cannot be undone.</AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction onClick={deleteAll} className="bg-destructive hover:bg-destructive/90">Delete all</AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </div>
          </motion.div>
        )}

        {view === "rag" && (
          <SubView key="rag" title="Knowledge base" onBack={() => setView("root")}>
            <label className="mb-4 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-surface/30 py-8 text-center hover:border-brand/40">
              <Upload className="h-5 w-5 text-muted-foreground" />
              <div className="text-[13px] font-medium">Upload files</div>
              <div className="text-xs text-muted-foreground">PDF, DOCX up to 20MB</div>
              <input type="file" className="hidden" onChange={() => toast.success("File uploaded", { description: "Indexing started." })} />
            </label>
            <div className="divide-y divide-border/60 rounded-xl border border-border/70 bg-surface/40">
              {docs.map((d) => (
                <div key={d.id} className="flex items-center justify-between px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-md bg-surface-2"><FileText className="h-3.5 w-3.5" /></div>
                    <div>
                      <div className="text-[13px] font-medium">{d.name}</div>
                      <div className="text-xs text-muted-foreground">{d.size}</div>
                    </div>
                  </div>
                  <button onClick={() => { setDocs((prev) => prev.filter((x) => x.id !== d.id)); toast(`${d.name} removed`); }} className="text-muted-foreground hover:text-destructive">
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </SubView>
        )}

        {view === "shared" && (
          <SubView key="shared" title="Shared links" onBack={() => setView("root")}>
            <div className="divide-y divide-border/60 rounded-xl border border-border/70 bg-surface/40">
              {shared.map((l) => (
                <div key={l.id} className="flex items-center justify-between px-4 py-3">
                  <div>
                    <div className="text-[13px] font-medium">{l.title}</div>
                    <div className="text-xs text-muted-foreground">Shared {l.when}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="ghost" onClick={() => toast("Opening link in new tab")}><ExternalLink className="mr-1 h-3 w-3" />View</Button>
                    <Button size="sm" variant="ghost" onClick={() => { setShared((p) => p.filter((x) => x.id !== l.id)); toast("Link revoked"); }} className="text-destructive hover:text-destructive">Revoke</Button>
                  </div>
                </div>
              ))}
            </div>
          </SubView>
        )}

        {view === "archived" && (
          <SubView key="archived" title="Archived chats" onBack={() => setView("root")}>
            <div className="divide-y divide-border/60 rounded-xl border border-border/70 bg-surface/40">
              {archived.map((a) => (
                <div key={a.id} className="flex items-center justify-between px-4 py-3">
                  <div>
                    <div className="text-[13px] font-medium">{a.title}</div>
                    <div className="text-xs text-muted-foreground">Archived {a.when}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="ghost" onClick={() => { setArchived((p) => p.filter((x) => x.id !== a.id)); toast.success("Chat unarchived"); }}>Unarchive</Button>
                    <Button size="sm" variant="ghost" onClick={() => { setArchived((p) => p.filter((x) => x.id !== a.id)); toast("Chat deleted"); }} className="text-destructive hover:text-destructive">Delete</Button>
                  </div>
                </div>
              ))}
            </div>
          </SubView>
        )}
      </AnimatePresence>
    </TabShell>
  );
}

function ManageRow({ title, description, onClick }: { title: string; description: string; onClick: () => void }) {
  return (
    <button onClick={onClick} className="flex w-full items-center justify-between gap-6 py-3.5 text-left">
      <div>
        <div className="text-[13px] font-medium">{title}</div>
        <div className="mt-0.5 text-xs text-muted-foreground">{description}</div>
      </div>
      <div className="flex items-center gap-1 text-xs text-muted-foreground">Manage <ChevronRight className="h-3.5 w-3.5" /></div>
    </button>
  );
}

function SubView({ title, onBack, children }: { title: string; onBack: () => void; children: React.ReactNode }) {
  return (
    <motion.div initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 8 }} transition={{ duration: 0.18 }}>
      <button onClick={onBack} className="mb-3 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground">
        <ChevronLeft className="h-3.5 w-3.5" /> Back to Data controls
      </button>
      <SectionTitle title={title} />
      {children}
    </motion.div>
  );
}
