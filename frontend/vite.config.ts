import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

const outDir = process.env.BEATVOTE_OUTDIR
  ? path.resolve(process.cwd(), process.env.BEATVOTE_OUTDIR)
  : path.resolve(process.cwd(), "../beatvote/static/app");

export default defineConfig({
  plugins: [react()],
  base: "/static/app/",
  build: {
    outDir,
    emptyOutDir: true,
    sourcemap: true
  },
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5000",
        changeOrigin: true
      }
    }
  }
});
