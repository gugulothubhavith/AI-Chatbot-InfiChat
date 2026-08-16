import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": "/src" } },
  server: {
    host: true,
    port: 5174,
    proxy: {
      // Lets `npm run dev` reach the backend on the same origin, so local work
      // exercises the same path production uses instead of depending on the
      // backend's CORS allowlist.
      "/api": {
        target: process.env.VITE_DEV_API_TARGET || "http://localhost:8000",
        changeOrigin: true,
        ws: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  build: {
    sourcemap: false,
    chunkSizeWarningLimit: 900,
    rollupOptions: {
      output: {
        // Route-level React.lazy already splits the pages. This additionally
        // pins the large shared libraries into stable chunks so editing one
        // page does not invalidate the vendor cache on every deploy.
        manualChunks: {
          react: ["react", "react-dom", "react-router-dom"],
          charts: ["recharts"],
          query: ["@tanstack/react-query"],
          motion: ["framer-motion"],
        },
      },
    },
  },
});
