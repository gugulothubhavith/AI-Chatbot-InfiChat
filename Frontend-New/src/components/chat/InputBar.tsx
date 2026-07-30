import { useRef, useState, type KeyboardEvent } from "react";
import { motion } from "framer-motion";
import { tapProps } from "@/lib/motion";
import { Paperclip, Mic, ArrowUp, Square, Globe, ImagePlus, Telescope, Brain, ChevronDown, Check, SlidersHorizontal, X } from "lucide-react";
import { toast } from "sonner";
import { useSettingsStore } from "@/stores/settings";
import { useModelStore, BUILTIN_MODELS, type ToolId, type ModelId } from "@/stores/model";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const toolMeta: Record<ToolId, { label: string; icon: typeof Globe }> = {
  research: { label: "Deep Research", icon: Telescope },
  thinking: { label: "Deep Thinking", icon: Brain },
  web: { label: "Web Search", icon: Globe },
  
  image: { label: "Image Gen", icon: ImagePlus },
};

const providerColor: Record<string, string> = {
  NVIDIA: "#76B900",
  Meta: "#0064E0",
  OpenAI: "#10a37f",
};

export function InputBar({
  onSubmit,
  onStop,
  pending,
  placeholder = "Message InfiChat…",
  hideTools = false,
}: {
  onSubmit: (v: string) => void;
  onStop?: () => void;
  pending: boolean;
  placeholder?: string;
  hideTools?: boolean;
}) {

  const [value, setValue] = useState("");
  const [recording, setRecording] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const ref = useRef<HTMLTextAreaElement>(null);
  const enterToSend = useSettingsStore((s) => s.enterToSend);
  const model = useModelStore((s) => s.model);
  const setModel = useModelStore((s) => s.setModel);
  const tools = useModelStore((s) => s.tools);
  const toggleTool = useModelStore((s) => s.toggleTool);

  const customModels = useModelStore((s) => s.customModels);
  const combined = [...BUILTIN_MODELS, ...customModels];
  const activeModel = combined.find((m) => m.id === model) ?? combined[0];
  const activeToolCount = (Object.keys(tools) as ToolId[]).filter((t) => tools[t]).length;

  const send = () => {
    const v = value.trim();
    if (!v || pending) return;
    onSubmit(v);
    setValue("");
    if (ref.current) ref.current.style.height = "auto";
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && enterToSend) {
      e.preventDefault();
      send();
    }
  };

  const autoresize = (el: HTMLTextAreaElement) => {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  };

  return (
    <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 flex justify-center px-4 pb-6">
      <div className="pointer-events-auto glass w-full max-w-3xl rounded-2xl p-2">
        <textarea
          ref={ref}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
            autoresize(e.target);
          }}
          onKeyDown={onKey}
          placeholder={placeholder}
          rows={1}
          className="min-h-9 w-full resize-none bg-transparent px-2 py-2 text-sm leading-relaxed outline-none placeholder:text-muted-foreground"
        />
        <div className="mt-1 flex items-center gap-1">
          <input 
            type="file" 
            ref={fileInputRef} 
            className="hidden" 
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                // In a real app, this would attach the file to the state
                toast.success(`Attached ${e.target.files[0].name}`);
              }
            }}
          />
          <motion.button
            {...tapProps}
            onClick={() => fileInputRef.current?.click()}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-muted-foreground hover:bg-surface-2 hover:text-foreground"
          >
            <Paperclip className="h-4 w-4" />
          </motion.button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <motion.button
                {...tapProps}
                className="group flex h-8 items-center gap-1.5 rounded-full px-2.5 text-[11px] font-medium text-muted-foreground hover:bg-surface-2 hover:text-foreground"
              >
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ background: providerColor[activeModel.provider] ?? "#888" }}
                />
                <span className="text-foreground">{activeModel.name}</span>
                <ChevronDown className="h-3 w-3 opacity-60 transition-transform duration-200 group-data-[state=open]:rotate-180" />
              </motion.button>

            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-72">
              {combined.map((m) => (
                <DropdownMenuItem
                  key={m.id}
                  onSelect={() => setModel(m.id as ModelId)}
                  className="flex items-start gap-2"
                >
                  <span
                    className="mt-1 h-2 w-2 shrink-0 rounded-full"
                    style={{ background: providerColor[m.provider] ?? "#888" }}
                  />
                  <div className="flex-1">
                    <div className="text-[13px]">{m.name}</div>
                    <div className="text-[11px] text-muted-foreground">{m.desc}</div>
                  </div>
                  <span className="text-[10px] text-muted-foreground">{m.provider}</span>
                  {model === m.id && <Check className="ml-1 h-3.5 w-3.5 text-brand" />}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>

          {!hideTools && (
            <>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <motion.button
                    {...tapProps}
                    className="group flex h-8 items-center gap-1.5 rounded-full px-2.5 text-[11px] font-medium text-muted-foreground hover:bg-surface-2 hover:text-foreground"
                  >
                    <SlidersHorizontal className="h-3 w-3" />
                    <span className="text-foreground">Tools</span>
                    {activeToolCount > 0 && (
                      <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-brand/15 px-1 text-[10px] font-semibold text-brand">
                        {activeToolCount}
                      </span>
                    )}
                    <ChevronDown className="h-3 w-3 opacity-60 transition-transform duration-200 group-data-[state=open]:rotate-180" />
                  </motion.button>

                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-64">
                  {(Object.keys(toolMeta) as ToolId[]).map((t) => {
                    const active = tools[t];
                    const M = toolMeta[t];
                    return (
                      <DropdownMenuItem
                        key={t}
                        onSelect={() => toggleTool(t)}
                        className="flex items-center gap-2"
                      >
                        <M.icon className={`h-3.5 w-3.5 ${active ? "text-brand" : "text-muted-foreground"}`} />
                        <span className="flex-1 text-[13px]">{M.label}</span>
                        {active && <Check className="h-3.5 w-3.5 text-brand" />}
                      </DropdownMenuItem>
                    );
                  })}
                </DropdownMenuContent>
              </DropdownMenu>

              <div className="ml-1 flex flex-1 flex-wrap items-center gap-1 overflow-hidden">
                {(Object.keys(toolMeta) as ToolId[])
                  .filter((t) => tools[t])
                  .map((t) => {
                    const M = toolMeta[t];
                    return (
                      <motion.div
                        key={t}
                        {...tapProps}
                        className="group flex h-6 items-center gap-1 rounded-full bg-brand/15 pl-2 pr-1 text-[10.5px] font-medium text-foreground"
                      >
                        <M.icon className="h-3 w-3 text-brand" />
                        {M.label}
                        <button
                          type="button"
                          onClick={() => toggleTool(t)}
                          aria-label={`Remove ${M.label}`}
                          className="ml-0.5 flex h-4 w-4 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-brand/25 hover:text-foreground"
                        >
                          <X className="h-2.5 w-2.5" />
                        </button>
                      </motion.div>

                    );
                  })}
              </div>
            </>
          )}
          {hideTools && <div className="flex-1" />}



          <motion.button
            {...tapProps}
            onClick={() => {
              if (recording) {
                setRecording(false);
                return;
              }
              const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
              if (!SpeechRecognition) {
                toast.error("Speech recognition is not supported in this browser.");
                return;
              }
              const recognition = new SpeechRecognition();
              recognition.continuous = false;
              recognition.interimResults = true;
              recognition.onstart = () => {
                setRecording(true);
              };
              let finalTranscript = value;
              recognition.onresult = (event: any) => {
                let interim = "";
                let final = "";
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                  if (event.results[i].isFinal) {
                    final += event.results[i][0].transcript;
                  } else {
                    interim += event.results[i][0].transcript;
                  }
                }
                const newText = finalTranscript + (finalTranscript ? " " : "") + final + interim;
                setValue(newText);
              };
              recognition.onerror = (e: any) => {
                console.error(e);
                setRecording(false);
                toast.error("Speech recognition failed.");
              };
              recognition.onend = () => {
                setRecording(false);
              };
              recognition.start();
            }}
            className={`relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition-colors ${
              recording ? "bg-destructive/15 text-destructive" : "text-muted-foreground hover:bg-surface-2 hover:text-foreground"
            }`}
          >
            {recording && <span className="absolute inset-0 rounded-xl bg-destructive/30 pulse-ring" />}
            <Mic className="h-4 w-4" />
          </motion.button>
          <motion.button
            {...tapProps}
            type="button"
            onClick={() => {
              if (pending) {
                onStop?.();
              } else {
                send();
              }
            }}
            disabled={!pending && !value.trim()}
            aria-label={pending ? "Stop generating" : "Send message"}
            className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl elevated disabled:opacity-40 ${
              pending
                ? "bg-destructive text-destructive-foreground hover:bg-destructive/90"
                : "bg-primary text-primary-foreground"
            }`}
          >
            {pending ? <Square className="h-3.5 w-3.5 fill-current" /> : <ArrowUp className="h-4 w-4" />}
          </motion.button>
        </div>
      </div>

    </div>
  );
}
