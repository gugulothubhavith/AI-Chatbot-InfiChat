import { motion, AnimatePresence } from "framer-motion";
import { Globe, Loader2, AlertTriangle, ExternalLink } from "lucide-react";
import type { WebSearchState, WebSearchSource, WebSearchCitation } from "@/hooks/useWebSearchStream";
import { Markdown } from "@/components/chat/Markdown";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

function hostOf(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function faviconFor(s: WebSearchSource) {
  return s.favicon ?? `https://www.google.com/s2/favicons?domain=${hostOf(s.url)}&sz=64`;
}

function SourceCard({ source, index }: { source: WebSearchSource; index: number }) {
  return (
    <motion.a
      href={source.url}
      target="_blank"
      rel="noreferrer"
      initial={{ opacity: 0, y: 8, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0 }}
      className="group relative flex min-w-[180px] max-w-[220px] shrink-0 flex-col gap-1.5 rounded-xl border border-border/60 bg-surface/60 p-2.5 hover:border-brand/40"
    >
      <div className="flex items-center gap-1.5">
        <span className="flex h-4 w-4 items-center justify-center rounded bg-surface-2 font-mono text-[9px] text-muted-foreground">
          {index}
        </span>
        <img src={faviconFor(source)} alt="" className="h-3.5 w-3.5 rounded-sm" />
        <span className="truncate text-[10.5px] text-muted-foreground">{hostOf(source.url)}</span>
      </div>
      <div className="line-clamp-2 text-[11.5px] font-medium leading-snug group-hover:text-brand">
        {source.title}
      </div>
    </motion.a>
  );
}

function CitedMarkdown({
  content,
  citations,
}: {
  content: string;
  citations: WebSearchCitation[];
}) {
  const map = new Map(citations.map((c) => [c.index, c]));
  // Replace [n] with a marker we can hydrate; we do this by wrapping in HTML via post-render.
  // Simpler: transform to markdown links to the source, then override rendering.
  const transformed = content.replace(/\[(\d+)\]/g, (m, num) => {
    const c = map.get(Number(num));
    if (!c) return m;
    return ` [\`${num}\`](${c.url} "${c.title.replace(/"/g, "'")}")`;
  });

  return (
    <TooltipProvider delayDuration={100}>
      <div className="citation-md">
        <Markdown content={transformed} />
      </div>
      {/* Fallback: also render citation strip so users see mapping */}
      <div className="mt-4 flex flex-wrap gap-1.5 border-t border-border/60 pt-3">
        {citations.map((c) => (
          <Tooltip key={c.index}>
            <TooltipTrigger asChild>
              <a
                href={c.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 rounded-full border border-border/60 bg-surface/60 px-2 py-0.5 text-[10.5px] text-muted-foreground hover:border-brand/40 hover:text-foreground"
              >
                <span className="font-mono text-brand">{c.index}</span>
                <span className="max-w-[140px] truncate">{hostOf(c.url)}</span>
                <ExternalLink className="h-2.5 w-2.5" />
              </a>
            </TooltipTrigger>
            <TooltipContent side="top" className="max-w-[240px] text-[11px]">
              {c.title}
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </TooltipProvider>
  );
}

export function WebSearchProgress({ state }: { state: WebSearchState }) {
  const showSpinner = !state.complete && !state.error;

  return (
    <div className="rounded-2xl border border-border bg-surface-2/40 p-4 backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-brand/10">
          <motion.div
            className="absolute inset-0 rounded-xl bg-brand/20 blur-md"
            animate={{ opacity: state.complete ? 0 : [0.2, 0.7, 0.2] }}
            transition={{ duration: 2, repeat: state.complete ? 0 : Infinity }}
          />
          <Globe className="relative h-4 w-4 text-brand" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-[11px] font-medium uppercase tracking-widest text-muted-foreground">
            Fast Web Search
          </div>
          <div className="flex min-h-[18px] items-center gap-2">
            {showSpinner && <Loader2 className="h-3 w-3 animate-spin text-brand" />}
            <AnimatePresence mode="wait">
              <motion.div
                key={state.currentStatus || (state.complete ? "done" : "idle")}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.2 }}
                className="truncate text-[13px] text-foreground"
              >
                {state.currentStatus || (state.complete ? "Done" : "Preparing…")}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Sources rail */}
      {state.sources.length > 0 && (
        <div className="mt-4">
          <div className="mb-2 flex items-center gap-2 text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
            <Globe className="h-3 w-3" /> Sources
            <span className="rounded-full bg-surface px-1.5 text-[10px] text-foreground/70">
              {state.sources.length}
            </span>
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1 [scrollbar-width:thin]">
            <AnimatePresence initial={false}>
              {state.sources.map((s, i) => (
                <SourceCard key={s.url} source={s} index={i + 1} />
              ))}
            </AnimatePresence>
          </div>
        </div>
      )}

      {/* Error */}
      {state.error && (
        <div className="mt-4 flex items-start gap-2 rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-[12px] text-destructive">
          <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
          <div>{state.error}</div>
        </div>
      )}

      {/* Report */}
      <AnimatePresence>
        {state.report && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 rounded-xl border border-border/60 bg-surface/60 p-4"
          >
            <CitedMarkdown content={state.report.content} citations={state.report.citations} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
