import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Download } from "lucide-react";
import { CodeBlock } from "./CodeBlock";

function slugify(s: string) {
  return (
    s
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 60) || "image"
  );
}

function downloadImage(src: string, alt: string) {
  const a = document.createElement("a");
  a.href = src;
  a.download = `infichat-${slugify(alt)}-${Date.now()}.png`;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

export function Markdown({ content }: { content: string }) {
  return (
    <div className="prose prose-sm prose-invert max-w-none prose-p:my-2 prose-p:leading-relaxed prose-headings:font-medium prose-headings:tracking-tight prose-code:before:content-none prose-code:after:content-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || "");
            if (inline) {
              return (
                <code className="rounded bg-surface-2 px-1 py-0.5 font-mono text-[12px]" {...props}>
                  {children}
                </code>
              );
            }
            return <CodeBlock language={match?.[1]} value={String(children).replace(/\n$/, "")} />;
          },
          img({ src, alt }: any) {
            const url = typeof src === "string" ? src : "";
            const label = alt || "image";
            const isFinal = url.startsWith("data:image");
            return (
              <span className="not-prose group relative my-3 block overflow-hidden rounded-xl border border-border bg-surface-1">
                <img
                  src={url}
                  alt={label}
                  className="block h-auto w-full max-w-[560px]"
                  loading="lazy"
                />
                {isFinal && (
                  <button
                    type="button"
                    onClick={() => downloadImage(url, label)}
                    className="absolute right-2 top-2 inline-flex items-center gap-1.5 rounded-md border border-border bg-surface-2/90 px-2.5 py-1.5 text-[11px] font-medium text-fg backdrop-blur-md transition-all hover:bg-surface-3 opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
                    aria-label="Download image"
                  >
                    <Download className="h-3.5 w-3.5" />
                    Download PNG
                  </button>
                )}
              </span>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
