import { createFileRoute } from "@tanstack/react-router";
import { motion, AnimatePresence } from "framer-motion";
import { tapProps } from "@/lib/motion";
import { Image as ImageIcon, Loader2 } from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import { useState } from "react";
import { api } from "@/lib/api";

export const Route = createFileRoute("/_app/image")({
  head: () => ({
    meta: [
      { title: "Image Gen — InfiChat" },
      { name: "description", content: "Generate stunning images from natural language." },
      { property: "og:title", content: "Image Gen — InfiChat" },
      { property: "og:description", content: "Generate stunning images from natural language." },
    ],
  }),
  component: ImagePage,
});

const initialGallery = [
  "/images/cyber_city.png",
  "/images/neon_whale.png",
  "/images/samurai_sunset.png",
  "/images/mech_warrior.png",
  "/images/mystical_forest.png",
  "/images/astronaut_cat.png",
];

function ImagePage() {
  const [prompt, setPrompt] = useState("");
  const [images, setImages] = useState<string[]>(initialGallery);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    try {
      const res = await api.fetchJSON<{ image_url: string; prompt: string }>("/image/generate", {
        method: "POST",
        body: JSON.stringify({ prompt: prompt.trim() }),
      });
      if (res.image_url) {
        setImages((prev) => [res.image_url, ...prev]);
      }
    } catch (err) {
      console.error("Image generation failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative h-full overflow-y-auto">
      <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex justify-start pt-4 pl-5">
        <span className="select-none font-bold text-foreground leading-none" style={{ fontSize: 18, letterSpacing: "-0.015em" }}>InfiChat</span>
      </div>
      <div className="mx-auto max-w-5xl px-8 py-16">

        <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
          <ImageIcon className="h-3 w-3" /> Image Gen
        </div>
        <h1 className="text-3xl font-medium tracking-tight">Compose an image</h1>
        <p className="mt-2 text-sm text-muted-foreground">Describe what you want. Adjust style, aspect, and seed.</p>

        <div className="mt-8 flex gap-2 rounded-2xl border border-border bg-surface p-2 elevated">
          <input 
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
            disabled={loading}
            placeholder="A cinematic shot of a whale gliding through neon fog…" 
            className="flex-1 bg-transparent px-3 text-sm outline-none placeholder:text-muted-foreground" 
          />
          <motion.button 
            {...tapProps} 
            onClick={handleGenerate}
            disabled={loading || !prompt.trim()}
            className="rounded-xl bg-primary px-4 py-2 text-xs font-medium text-primary-foreground elevated disabled:opacity-50 flex items-center gap-2"
          >
            {loading && <Loader2 className="h-3 w-3 animate-spin" />}
            {loading ? "Generating..." : "Generate"}
          </motion.button>
        </div>

        <div className="mt-10 grid grid-cols-3 gap-3">
          <AnimatePresence mode="popLayout">
            {images.map((imgUrl, i) => (
              <motion.div 
                key={imgUrl + i} 
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                whileHover={{ y: -2 }} 
                className="aspect-square rounded-xl elevated overflow-hidden bg-surface"
              >
                <img src={imgUrl} alt={`Generated ${i}`} className="w-full h-full object-cover" />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
