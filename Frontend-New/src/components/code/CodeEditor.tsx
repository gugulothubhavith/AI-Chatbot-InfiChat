import { useEffect, useRef } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import type { GenFile } from "@/hooks/useCodeSquad";
import { motion } from "framer-motion";

const langFor = (path: string) => {
  if (path.endsWith(".tsx") || path.endsWith(".ts")) return "tsx";
  if (path.endsWith(".jsx") || path.endsWith(".js")) return "jsx";
  if (path.endsWith(".css")) return "css";
  if (path.endsWith(".json")) return "json";
  if (path.endsWith(".md")) return "markdown";
  if (path.endsWith(".html")) return "html";
  return "text";
};

export function CodeEditor({ file }: { file: GenFile | null }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (file?.generating && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [file?.content, file?.generating]);

  if (!file) {
    return (
      <div className="flex h-full items-center justify-center rounded-xl border border-border bg-[#0d1117] text-[12px] text-white/40">
        Select a file to view
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-xl border border-border bg-[#0d1117]">
      <div className="flex items-center justify-between border-b border-white/5 px-3 py-2">
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#febc2e]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#28c840]" />
          <span className="ml-3 font-mono text-[11px] text-white/70">{file.path}</span>
        </div>
        {file.generating && (
          <motion.span
            className="flex items-center gap-1 rounded-full bg-brand/20 px-2 py-0.5 font-mono text-[10px] text-brand"
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1.2, repeat: Infinity }}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-brand" />
            streaming
          </motion.span>
        )}
      </div>
      <div ref={scrollRef} className="min-h-0 flex-1 overflow-auto">
        <SyntaxHighlighter
          language={langFor(file.path)}
          style={vscDarkPlus}
          showLineNumbers
          customStyle={{ margin: 0, background: "transparent", padding: "12px 14px", fontSize: 12.5 }}
          codeTagProps={{ style: { fontFamily: "var(--font-mono)" } }}
        >
          {file.content || " "}
        </SyntaxHighlighter>
      </div>
    </div>
  );
}
