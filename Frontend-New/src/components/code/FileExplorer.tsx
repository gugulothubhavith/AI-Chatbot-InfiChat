import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, Download, File as FileIcon, Folder, FolderOpen, Search } from "lucide-react";
import { tapProps } from "@/lib/motion";
import type { GenFile } from "@/hooks/useCodeSquad";
import JSZip from "jszip";
import fileSaver from "file-saver";
const { saveAs } = fileSaver;

type TreeNode = {
  name: string;
  path: string;
  isDir: boolean;
  children?: Record<string, TreeNode>;
};

function buildTree(files: GenFile[]): TreeNode {
  const root: TreeNode = { name: "", path: "", isDir: true, children: {} };
  for (const f of files) {
    const parts = f.path.split("/").filter(Boolean);
    let cur = root;
    parts.forEach((part, idx) => {
      const isLast = idx === parts.length - 1;
      cur.children = cur.children ?? {};
      if (!cur.children[part]) {
        cur.children[part] = {
          name: part,
          path: parts.slice(0, idx + 1).join("/"),
          isDir: !isLast,
          children: isLast ? undefined : {},
        };
      }
      cur = cur.children[part];
    });
  }
  return root;
}

export function FileExplorer({
  files,
  selectedPath,
  onSelect,
  flashPath,
}: {
  files: GenFile[];
  selectedPath: string | null;
  onSelect: (path: string) => void;
  flashPath?: string | null;
}) {
  const [query, setQuery] = useState("");
  const [openDirs, setOpenDirs] = useState<Record<string, boolean>>({ src: true, "src/components": true });

  const filtered = useMemo(() => {
    if (!query) return files;
    return files.filter((f) => f.path.toLowerCase().includes(query.toLowerCase()));
  }, [files, query]);

  const tree = useMemo(() => buildTree(filtered), [filtered]);

  const download = async () => {
    const zip = new JSZip();
    for (const f of files) zip.file(f.path, f.content);
    const blob = await zip.generateAsync({ type: "blob" });
    saveAs(blob, "infibuild-project.zip");
  };

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-xl border border-border bg-surface-2/40">
      <div className="flex items-center gap-2 border-b border-border/60 px-3 py-2">
        <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground">Explorer</span>
        <span className="rounded-full bg-surface px-1.5 font-mono text-[10px] text-foreground/70">{files.length}</span>
        <motion.button
          {...tapProps}
          onClick={download}
          disabled={files.length === 0}
          className="ml-auto flex h-6 items-center gap-1 rounded-md bg-brand/15 px-1.5 text-[10.5px] font-medium text-brand disabled:opacity-40"
        >
          <Download className="h-3 w-3" /> ZIP
        </motion.button>
      </div>
      <div className="border-b border-border/60 p-2">
        <div className="flex items-center gap-1.5 rounded-md bg-surface px-2 py-1">
          <Search className="h-3 w-3 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search files"
            className="w-full bg-transparent text-[11.5px] outline-none placeholder:text-muted-foreground"
          />
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-1.5 font-mono text-[11.5px]">
        {files.length === 0 ? (
          <div className="p-6 text-center text-[11px] text-muted-foreground">No files yet.</div>
        ) : (
          <TreeView
            node={tree}
            depth={0}
            openDirs={openDirs}
            toggle={(p) => setOpenDirs((s) => ({ ...s, [p]: !s[p] }))}
            selectedPath={selectedPath}
            onSelect={onSelect}
            flashPath={flashPath}
          />
        )}
      </div>
    </div>
  );
}

function TreeView({
  node,
  depth,
  openDirs,
  toggle,
  selectedPath,
  onSelect,
  flashPath,
}: {
  node: TreeNode;
  depth: number;
  openDirs: Record<string, boolean>;
  toggle: (p: string) => void;
  selectedPath: string | null;
  onSelect: (p: string) => void;
  flashPath?: string | null;
}) {
  const entries = Object.values(node.children ?? {}).sort((a, b) => {
    if (a.isDir !== b.isDir) return a.isDir ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
  return (
    <div>
      {entries.map((child) => {
        const open = openDirs[child.path] ?? depth < 1;
        if (child.isDir) {
          return (
            <div key={child.path}>
              <button
                onClick={() => toggle(child.path)}
                className="flex w-full items-center gap-1 rounded px-1.5 py-1 text-left hover:bg-surface"
                style={{ paddingLeft: 8 + depth * 12 }}
              >
                <ChevronRight
                  className={`h-3 w-3 text-muted-foreground transition-transform ${open ? "rotate-90" : ""}`}
                />
                {open ? <FolderOpen className="h-3.5 w-3.5 text-brand" /> : <Folder className="h-3.5 w-3.5 text-brand/80" />}
                <span className="truncate">{child.name}</span>
              </button>
              <AnimatePresence initial={false}>
                {open && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.18 }}
                  >
                    <TreeView
                      node={child}
                      depth={depth + 1}
                      openDirs={openDirs}
                      toggle={toggle}
                      selectedPath={selectedPath}
                      onSelect={onSelect}
                      flashPath={flashPath}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        }
        const selected = selectedPath === child.path;
        const flash = flashPath === child.path;
        return (
          <motion.button
            key={child.path}
            onClick={() => onSelect(child.path)}
            className={`flex w-full items-center gap-1.5 rounded px-1.5 py-1 text-left transition-colors ${
              selected ? "bg-brand/15 text-foreground" : "hover:bg-surface"
            }`}
            style={{ paddingLeft: 22 + depth * 12 }}
            animate={flash ? { backgroundColor: ["rgba(37,99,235,0.35)", "rgba(37,99,235,0)"] } : {}}
            transition={{ duration: 0.9 }}
          >
            <FileIcon className="h-3 w-3 text-muted-foreground" />
            <span className="truncate">{child.name}</span>
          </motion.button>
        );
      })}
    </div>
  );
}
