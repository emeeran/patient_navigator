import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/auth": "http://localhost:8000",
      "/patients": "http://localhost:8000",
      "/cases": "http://localhost:8000",
      "/documents": "http://localhost:8000",
      "/ai": "http://localhost:8000",
      "/hospitals": "http://localhost:8000",
      "/funding": "http://localhost:8000",
      "/followups": "http://localhost:8000",
      "/reviews": "http://localhost:8000",
      "/admin": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
