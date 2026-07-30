import { createFileRoute } from "@tanstack/react-router";

import { MessageFeed } from "@/components/chat/MessageFeed";
import { InputBar } from "@/components/chat/InputBar";
import { useChatStore } from "@/stores/chat";
import { useModelStore } from "@/stores/model";
import { useThinkingStream } from "@/hooks/useThinkingStream";
import { useResearchStream } from "@/hooks/useResearchStream";
import { useWebSearchStream } from "@/hooks/useWebSearchStream";
import { DeepThinkingProgress } from "@/components/thinking/DeepThinkingProgress";
import { DeepResearchProgress } from "@/components/research/DeepResearchProgress";
import { WebSearchProgress } from "@/components/websearch/WebSearchProgress";
import { useEffect, useRef, useState } from "react";

export const Route = createFileRoute("/_app/chat")({
  head: () => ({
    meta: [
      { title: "Chat — InfiChat" },
      { name: "description", content: "Chat with InfiChat across leading AI models." },
      { property: "og:title", content: "Chat — InfiChat" },
      { property: "og:description", content: "Chat with InfiChat across leading AI models." },
    ],
  }),
  component: ChatPage,
});

function ChatPage() {
  const send = useChatStore((s) => s.send);
  const stopChat = useChatStore((s) => s.stop);
  const appendUser = useChatStore((s) => s.appendUser);
  const appendAssistant = useChatStore((s) => s.appendAssistant);
  const updateAssistant = useChatStore((s) => s.updateAssistant);
  const setPending = useChatStore((s) => s.setPending);
  const chatPending = useChatStore((s) => s.pending);
  const tools = useModelStore((s) => s.tools);
  const toggleTool = useModelStore((s) => s.toggleTool);

  const thinking = useThinkingStream();
  const research = useResearchStream();
  const websearch = useWebSearchStream();
  const [mode, setMode] = useState<"thinking" | "research" | "web" | "image" | null>(null);
  const finalizedRef = useRef(false);
  const imageAbortRef = useRef<AbortController | null>(null);

  const streamPending = thinking.running || research.running || websearch.running;
  const pending = chatPending || streamPending;

  // finalize thinking
  useEffect(() => {
    if (mode !== "thinking") return;
    if (thinking.state.complete && !finalizedRef.current) {
      finalizedRef.current = true;
      const report = thinking.state.report;
      const chain = report?.reasoning_chain.map((r, i) => `**${i + 1}. ${r.title}**\n\n${r.content}`).join("\n\n") ?? "";
      appendAssistant(`${report?.executive_summary ?? ""}\n\n---\n\n### Reasoning chain\n\n${chain}`);
      setTimeout(() => {
        thinking.reset();
        setMode(null);
      }, 400);
    }
  }, [thinking, mode, appendAssistant]);

  // finalize research
  useEffect(() => {
    if (mode !== "research") return;
    if (research.state.complete && !finalizedRef.current) {
      finalizedRef.current = true;
      const report = research.state.report;
      const cites = report?.citations
        .map((c, i) => `[${i + 1}] [${c.title}](${c.url})`)
        .join("\n") ?? "";
      appendAssistant(`${report?.content ?? ""}\n\n---\n\n**References**\n\n${cites}`);
      setTimeout(() => {
        research.reset();
        setMode(null);
      }, 400);
    }
  }, [research, mode, appendAssistant]);

  // finalize web search
  useEffect(() => {
    if (mode !== "web") return;
    if (websearch.state.complete && !finalizedRef.current) {
      finalizedRef.current = true;
      const report = websearch.state.report;
      const cites =
        report?.citations
          .map((c) => `[${c.index}] [${c.title}](${c.url})`)
          .join("\n") ?? "";
      appendAssistant(`${report?.content ?? ""}${cites ? `\n\n---\n\n**Sources**\n\n${cites}` : ""}`);
      setTimeout(() => {
        websearch.reset();
        setMode(null);
        toggleTool("web");
      }, 400);
    }
  }, [websearch, mode, appendAssistant, toggleTool]);


  const handleSubmit = async (v: string) => {
    if (tools.thinking) {
      finalizedRef.current = false;
      appendUser(v);
      setMode("thinking");
      void thinking.start(v);
      return;
    }
    if (tools.research) {
      finalizedRef.current = false;
      appendUser(v);
      setMode("research");
      void research.start(v);
      return;
    }
    if (tools.web) {
      finalizedRef.current = false;
      appendUser(v);
      setMode("web");
      void websearch.start(v);
      return;
    }
    if (tools.image) {
      appendUser(v);
      setPending(true);
      setMode("image");
      const ctrl = new AbortController();
      imageAbortRef.current = ctrl;
      const msgId = appendAssistant(`🎨 **Generating your image...**`);
      try {
        const { api } = await import("@/lib/api");
        const res = await api.fetchJSON<{ image_url: string; prompt: string }>("/image/generate", {
          method: "POST",
          body: JSON.stringify({ prompt: v }),
          signal: ctrl.signal,
        });
        if (msgId && res.image_url) {
          updateAssistant(msgId, `Here's your image for **${v}**.\n\n![${v}](${res.image_url})`);
        }
      } catch (err) {
        const aborted = ctrl.signal.aborted || (err instanceof Error && err.name === "AbortError");
        if (msgId) {
          updateAssistant(
            msgId,
            aborted
              ? `_Image generation stopped._`
              : `⚠️ Image generation failed: ${err instanceof Error ? err.message : "unknown error"}`,
          );
        }
      } finally {
        imageAbortRef.current = null;
        setPending(false);
        setMode(null);
        toggleTool("image");
      }
      return;
    }
    void send(v);
  };

  const handleStop = () => {
    if (mode === "thinking") {
      thinking.cancel();
      finalizedRef.current = true;
      const partial = thinking.state.steps.map((s, i) => `**${i + 1}. ${s.title}**\n\n${s.content}`).join("\n\n");
      appendAssistant(`${partial || "_Stopped._"}\n\n_Deep Thinking stopped._`);
      thinking.reset();
      setMode(null);
      return;
    }
    if (mode === "research") {
      research.cancel();
      finalizedRef.current = true;
      const partial = research.state.findings.map((f) => `- ${f.claim} _(${Math.round(f.confidence * 100)}%)_`).join("\n");
      appendAssistant(`${partial || "_Stopped._"}\n\n_Deep Research stopped._`);
      research.reset();
      setMode(null);
      return;
    }
    if (mode === "web") {
      websearch.cancel();
      finalizedRef.current = true;
      const partial = websearch.state.report?.content ?? "_Stopped._";
      appendAssistant(`${partial}\n\n_Web Search stopped._`);
      websearch.reset();
      setMode(null);
      toggleTool("web");
      return;
    }
    if (mode === "image") {
      imageAbortRef.current?.abort();
      return;
    }
    stopChat();
  };

  const streamSlot =
    mode === "thinking" ? (
      <DeepThinkingProgress state={thinking.state} />
    ) : mode === "research" ? (
      <DeepResearchProgress state={research.state} />
    ) : mode === "web" ? (
      <WebSearchProgress state={websearch.state} />
    ) : null;

  return (
    <div className="relative h-full">
      <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex h-14 items-center pl-4">
        <span
          className="select-none font-bold text-foreground leading-none"
          style={{ fontSize: 18, letterSpacing: "-0.015em" }}
        >
          InfiChat
        </span>
      </div>

      <MessageFeed streamSlot={streamSlot} />
      <InputBar onSubmit={handleSubmit} onStop={handleStop} pending={pending} />
    </div>
  );
}

