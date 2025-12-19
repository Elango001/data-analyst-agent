import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/configure": "http://localhost:8000",
      "/configure-db": "http://localhost:8000",
      "/upload": "http://localhost:8000",
      "/clean": "http://localhost:8000",
      "/tool-logs": "http://localhost:8000",
      "/deleted-data": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});
