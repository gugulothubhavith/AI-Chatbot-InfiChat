import { useState } from "react";
import { Block, Row, SectionTitle, TabShell } from "./_primitives";
import { ConsentPanel } from "./ConsentPanel";
import { Button } from "@/components/ui/button";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { ChevronRight, ChevronLeft, Upload, Trash2, Download, ExternalLink, FileText, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
// Default import then destructure — the repo's existing idiom, per
// `components/code/FileExplorer.tsx`.
import fileSaver from "file-saver";
import { api, ApiError, API_ERROR_CODES } from "@/lib/api";
import { useChatStore } from "@/stores/chat";

const { saveAs } = fileSaver;

type View = "root" | "rag" | "shared" | "archived";

/**
 * Both data-rights endpoints below live in `chat.py`, which depends on
 * `require_consent`. A user whose consent has gone stale gets a 403 that raises
 * the re-consent modal instead of a result, so the failure has to name that
 * cause rather than telling them to try again.
 */
function failureDescription(err: unknown, fallback: string): string {
  if (err instanceof ApiError && err.code === API_ERROR_CODES.consentRequired) {
    return "Accept the updated policies first, then try again.";
  }
  return err instanceof Error ? err.message : fallback;
}

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
  const [exporting, setExporting] = useState(false);
  const [deleting, setDeleting] = useState(false);

  /**
   * GDPR Art. 15 / DPDP s.11 — hand over the copy, do not promise one.
   *
   * The previous handler said a download link was on its way and sent nothing.
   * This fetches the archive and saves it, and says so only once the file is
   * written.
   */
  async function exportData() {
    setExporting(true);
    try {
      const archive = await api.chat.exportChatHistory();
      const blob = new Blob([JSON.stringify(archive, null, 2)], {
        type: "application/json",
      });
      // `generated_at` is a tz-aware isoformat from the server and is always
      // populated, so the date prefix is safe to slice off it.
      saveAs(blob, `infichat-chat-export-${archive.generated_at.slice(0, 10)}.json`);
      toast.success("Export downloaded", {
        description: `${archive.sessions.length} conversation${archive.sessions.length === 1 ? "" : "s"} saved to your device.`,
      });
    } catch (err) {
      toast.error("Could not export your data", {
        description: failureDescription(err, "Please try again."),
      });
    } finally {
      setExporting(false);
    }
  }

  /**
   * GDPR Art. 17 / DPDP s.12 — erase every conversation, keeping the account.
   *
   * The toast follows the response rather than the click: this is irreversible,
   * and announcing it before the server has done it can report a deletion that
   * never happened.
   */
  async function deleteAll() {
    setDeleting(true);
    try {
      await api.chat.deleteChatHistory();
      // Every session the store holds was just deleted server-side, and the
      // cascade took the messages with it. Re-read rather than patch.
      await useChatStore.getState().loadSessions();
      toast.success("All chats deleted", {
        description: "Every conversation has been permanently removed.",
      });
    } catch (err) {
      toast.error("Could not delete your chats", {
        description: failureDescription(err, "Please try again."),
      });
    } finally {
      setDeleting(false);
    }
  }

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
              <Row title="Export your data" description="Download a JSON archive of every conversation and message on your account.">
                <Button size="sm" variant="outline" onClick={exportData} disabled={exporting}>
                  {exporting ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : <Download className="mr-1.5 h-3.5 w-3.5" />}
                  {exporting ? "Preparing" : "Download"}
                </Button>
              </Row>
            </Block>

            <div className="h-6" />
            <ConsentPanel />

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
                    {/* The in-flight guard sits on the trigger, not the action:
                        Radix closes the dialog the moment the action is clicked,
                        so a disabled state there would never be seen. */}
                    <Button size="sm" variant="destructive" disabled={deleting}>
                      {deleting ? <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" /> : null}
                      Delete all
                    </Button>
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
