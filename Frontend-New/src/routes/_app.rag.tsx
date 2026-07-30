import { createFileRoute } from "@tanstack/react-router";
import { Database, Upload, FileText, Search, Loader2, Trash2 } from "lucide-react";
import { motion } from "framer-motion";
import { tapProps } from "@/lib/motion";
import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";

export const Route = createFileRoute("/_app/rag")({
  head: () => ({
    meta: [
      { title: "RAG — InfiChat" },
      { name: "description", content: "Bring your own documents. Retrieve, cite, chat." },
      { property: "og:title", content: "RAG — InfiChat" },
      { property: "og:description", content: "Bring your own documents. Retrieve, cite, chat." },
    ],
  }),
  component: RagPage,
});

function RagPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [query, setQuery] = useState("");
  const [queryLoading, setQueryLoading] = useState(false);
  const [results, setResults] = useState<string[]>([]);
  const [documents, setDocuments] = useState<{ filename: string; chunk_count?: number }[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load documents on mount
  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const res = await api.fetchJSON<{ documents: { filename: string; chunk_count?: number }[] }>("/rag/documents");
      setDocuments(res.documents || []);
    } catch {
      // Backend may not have documents endpoint — non-fatal
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      const token = (() => {
        try {
          const raw = localStorage.getItem("infichat-auth");
          if (!raw) return null;
          return JSON.parse(raw)?.state?.token ?? null;
        } catch { return null; }
      })();

      await fetch(`${(import.meta.env.VITE_API_URL as string) || "/api/v1"}/rag/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      await loadDocuments();
    } catch (err: any) {
      console.error("Upload failed:", err);
    } finally {
      setUploading(false);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) return;
    setQueryLoading(true);
    try {
      const res = await api.fetchJSON<{ results: string[] }>("/rag/query", {
        method: "POST",
        body: JSON.stringify({ query: query.trim() }),
      });
      setResults(res.results || []);
    } catch (err: any) {
      console.error("Query failed:", err);
    } finally {
      setQueryLoading(false);
    }
  };

  const handleDelete = async (filename: string) => {
    try {
      await api.fetchJSON(`/rag/documents/${encodeURIComponent(filename)}`, { method: "DELETE" });
      await loadDocuments();
    } catch (err: any) {
      console.error("Delete failed:", err);
    }
  };

  return (
    <div className="relative h-full overflow-y-auto">
      <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex justify-start pt-4 pl-5">
        <span className="select-none font-bold text-foreground leading-none" style={{ fontSize: 18, letterSpacing: "-0.015em" }}>InfiChat</span>
      </div>
      <div className="mx-auto max-w-4xl px-8 py-16">

        <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
          <Database className="h-3 w-3" /> Knowledge
        </div>
        <h1 className="text-3xl font-medium tracking-tight">RAG</h1>
        <p className="mt-2 text-sm text-muted-foreground">Upload documents. InfiChat will embed, index, and cite them in your chats.</p>

        {/* Upload Area */}
        <motion.div
          {...tapProps}
          onClick={() => fileInputRef.current?.click()}
          className="mt-8 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-border bg-surface-2/40 py-12 text-sm text-muted-foreground hover:bg-surface-2/70"
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".pdf,.docx,.md,.txt"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          {file ? (
            <>
              <FileText className="h-5 w-5 text-brand" />
              <span className="font-medium text-foreground">{file.name}</span>
              <span className="text-[11px]">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
            </>
          ) : (
            <>
              <Upload className="h-5 w-5" />
              Drop files here, or click to browse
              <span className="text-[11px]">PDF, DOCX, MD, TXT · up to 200 MB</span>
            </>
          )}
        </motion.div>

        {file && (
          <motion.button
            {...tapProps}
            onClick={handleUpload}
            disabled={uploading}
            className="mt-3 w-full rounded-xl bg-primary py-2.5 text-sm font-medium text-primary-foreground elevated disabled:opacity-50"
          >
            {uploading ? "Uploading…" : "Upload to Knowledge Base"}
          </motion.button>
        )}

        {/* Query Section */}
        <div className="mt-10">
          <div className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">Ask your documents</div>
          <div className="flex gap-2 rounded-2xl border border-border bg-surface p-2 elevated">
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleQuery()}
              placeholder="What is discussed in the document?"
              className="flex-1 bg-transparent px-3 text-sm outline-none placeholder:text-muted-foreground"
            />
            <motion.button
              {...tapProps}
              onClick={handleQuery}
              disabled={queryLoading || !query.trim()}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground elevated disabled:opacity-50"
            >
              {queryLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            </motion.button>
          </div>

          {results.length > 0 && (
            <div className="mt-4 space-y-2">
              {results.map((r, i) => (
                <div key={i} className="rounded-xl border border-border bg-surface-2/40 p-4 text-sm leading-relaxed">
                  {r}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Indexed Documents */}
        <div className="mt-10">
          <div className="mb-3 text-xs font-medium uppercase tracking-wider text-muted-foreground">Indexed</div>
          {documents.length > 0 ? (
            <div className="overflow-hidden rounded-xl border border-border">
              {documents.map((d, i) => (
                <div key={d.filename} className={`flex items-center gap-3 px-4 py-3 text-sm ${i ? "border-t border-border" : ""}`}>
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span className="flex-1">{d.filename}</span>
                  {d.chunk_count != null && (
                    <span className="text-xs text-muted-foreground">{d.chunk_count} chunks</span>
                  )}
                  <motion.button
                    {...tapProps}
                    onClick={() => handleDelete(d.filename)}
                    className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                  >
                    <Trash2 className="h-3 w-3" />
                  </motion.button>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border py-12 text-muted-foreground">
              <Database className="h-8 w-8 mb-2 opacity-30" />
              <p className="text-sm font-medium">No documents indexed yet</p>
              <p className="text-xs mt-1">Upload a document to get started</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
