import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5174,
    proxy: {
      "/auth": "http://localhost:8001",
      "/patients": "http://localhost:8001",
      "/cases": "http://localhost:8001",
      "/documents": "http://localhost:8001",
      "/ai": "http://localhost:8001",
      "/hospitals": "http://localhost:8001",
      "/funding": "http://localhost:8001",
      "/followups": "http://localhost:8001",
      "/reviews": "http://localhost:8001",
      "/admin": "http://localhost:8001",
      "/health": "http://localhost:8001",
    },
  },
});
