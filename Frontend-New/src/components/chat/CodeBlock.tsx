import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export function CodeBlock({ language, value }: { language?: string; value: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="my-3 overflow-hidden rounded-xl border border-border bg-[#0d1117]">
      <div className="flex items-center justify-between border-b border-white/5 px-3 py-2">
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#febc2e]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#28c840]" />
          <span className="ml-3 font-mono text-[10px] uppercase tracking-widest text-white/50">
            {language ?? "text"}
          </span>
        </div>
        <button
          onClick={() => {
            navigator.clipboard?.writeText(value);
            setCopied(true);
            setTimeout(() => setCopied(false), 1600);
          }}
          className="flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-white/70 hover:bg-white/5 hover:text-white"
        >
          <AnimatePresence mode="wait" initial={false}>
            {copied ? (
              <motion.span key="c" initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} className="flex items-center gap-1">
                <Check className="h-3 w-3" /> Copied
              </motion.span>
            ) : (
              <motion.span key="cp" initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} className="flex items-center gap-1">
                <Copy className="h-3 w-3" /> Copy
              </motion.span>
            )}
          </AnimatePresence>
        </button>
      </div>
      <SyntaxHighlighter
        language={language || "text"}
        style={oneDark}
        customStyle={{ margin: 0, background: "transparent", padding: "14px 16px", fontSize: 12.5 }}
        codeTagProps={{ style: { fontFamily: "var(--font-mono)" } }}
      >
        {value.replace(/\n$/, "")}
      </SyntaxHighlighter>
    </div>
  );
}
