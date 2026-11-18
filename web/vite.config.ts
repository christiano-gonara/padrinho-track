import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  base: mode === "pages" ? "/padrinho-track/" : "/",
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:5000",
      "/relatorio": "http://127.0.0.1:5000",
      "/match/lista-contatos": "http://127.0.0.1:5000"
    }
  },
  build: {
    outDir: "dist",
    emptyOutDir: true
  }
}));
