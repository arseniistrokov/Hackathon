import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import path from "node:path"

// Один процесс в проде: FastAPI раздаёт frontend/dist с "/". В dev — прокси /api на uvicorn.
export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  build: { outDir: "dist", emptyOutDir: true },
  server: {
    port: 5173,
    proxy: { "/api": { target: "http://127.0.0.1:8000", changeOrigin: true } },
  },
})
