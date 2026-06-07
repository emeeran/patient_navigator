import { defineConfig, type UserConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { readFileSync } from "fs";
import { resolve } from "path";

// Read dynamic backend port written by dev.sh (falls back to 8002)
const backendPort = (() => {
  try {
    return readFileSync(resolve(__dirname, "../.dev-pids/backend.port"), "utf8").trim();
  } catch {
    return "8002";
  }
})();

const proxyTarget = `http://localhost:${backendPort}`;

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5174,
    proxy: {
      "/auth": proxyTarget,
      "/patients": proxyTarget,
      "/cases": proxyTarget,
      "/documents": proxyTarget,
      "/ai": proxyTarget,
      "/hospitals": proxyTarget,
      "/funding": proxyTarget,
      "/followups": proxyTarget,
      "/reviews": proxyTarget,
      "/admin/dedup": proxyTarget,
      "/admin/scrape": proxyTarget,
      "/admin/import": proxyTarget,
      "/admin/users": proxyTarget,
      "/admin/settings": proxyTarget,
      "/admin/audit-log": proxyTarget,
      "/admin/database": proxyTarget,
      "/health": proxyTarget,
    },
  },
  build: {
    sourcemap: true,
    minify: "terser",
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules/react-dom") || id.includes("node_modules/react/")) return "vendor";
          if (id.includes("node_modules/react-router")) return "vendor";
          if (id.includes("node_modules/@tanstack")) return "query";
          if (id.includes("node_modules/axios")) return "api";
        },
      },
    },
  },
} satisfies UserConfig);
