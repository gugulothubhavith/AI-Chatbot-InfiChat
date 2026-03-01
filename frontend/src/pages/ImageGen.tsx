import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import axios from "axios";
import { Button } from "../components/ui/Button";
import { Logo } from "../components/Logo";
import { Sparkles, Loader2, Download } from "lucide-react";

export default function ImageGen() {
  const { token } = useAuth();
  const [prompt, setPrompt] = useState("");
  const [images, setImages] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);

    try {
      const res = await axios.post(
        "/api/image/generate",
        { prompt },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setImages((prev) => [res.data.image_url, ...prev]);
    } catch (err: any) {
      alert(`Generation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (url: string, index: number) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `generated-image-${Date.now()}-${index}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error("Download failed, opening in new tab:", error);
      window.open(url, '_blank');
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#0B1120] text-gray-900 dark:text-white overflow-hidden transition-colors duration-300">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white/80 dark:bg-[#0B1120]/50 backdrop-blur-md sticky top-0 z-10 border-b border-white/0 dark:border-white/0">
        <div className="flex items-center gap-4">
          <Logo hideIcon={true} nameSize={22} className="ml-[-8px]" />
          <div className="h-5 w-px bg-gray-300 dark:bg-gray-700"></div>
          <h1 className="font-semibold text-gray-900 dark:text-white text-lg tracking-tight">Image Generation</h1>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 md:p-8 bg-gray-50 dark:bg-[#0B1120]">
        <div className="max-w-6xl mx-auto space-y-8">


          {/* Input Section */}
          <div className="bg-white dark:bg-gray-900/50 p-6 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm relative overflow-hidden group transition-colors duration-200">
            <div className="absolute inset-0 bg-gradient-to-r from-pink-500/5 to-rose-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="flex gap-4 relative z-10">
              <input
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
                disabled={loading}
                placeholder="Describe the image you want to generate... (e.g., 'A cyberpunk city in rain, neon lights')"
                className="flex-1 w-full h-14 px-4 text-base bg-gray-50 dark:bg-gray-950/50 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white rounded-xl focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all placeholder:text-gray-400"
              />
              <Button
                onClick={handleGenerate}
                disabled={loading || !prompt.trim()}
                className="h-14 px-8 rounded-xl bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 text-white shadow-lg shadow-pink-500/20"
              >
                {loading ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : <Sparkles className="mr-2 h-5 w-5" />}
                Generate
              </Button>
            </div>
          </div>

          {/* Gallery */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {loading && (
              <div className="aspect-square rounded-2xl bg-gray-100 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 animate-pulse flex items-center justify-center transition-colors duration-200">
                <div className="flex flex-col items-center gap-2 text-gray-500">
                  <Loader2 className="h-8 w-8 animate-spin text-pink-500" />
                  <span className="text-sm font-medium">Dreaming...</span>
                </div>
              </div>
            )}

            {images.map((img, idx) => (
              <div key={idx} className="group relative aspect-square rounded-2xl overflow-hidden bg-gray-100 dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-lg transition-all hover:scale-[1.02] hover:shadow-pink-500/10 hover:border-pink-500/50">
                <img
                  src={img}
                  alt={`Generated ${idx}`}
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-4 backdrop-blur-sm">
                  <Button variant="secondary" size="sm" className="rounded-full" onClick={() => handleDownload(img, idx)}>
                    <Download className="h-4 w-4 mr-2" />
                    Download
                  </Button>
                </div>
              </div>
            ))}

            {!loading && images.length === 0 && (
              <div className="col-span-full py-20 flex flex-col items-center justify-center text-gray-500 border-2 border-dashed border-gray-200 dark:border-gray-800 rounded-2xl bg-gray-50 dark:bg-gray-900/20 transition-colors duration-200">
                <Sparkles className="h-10 w-10 mb-4 opacity-20" />
                <p>Your generated images will appear here</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
