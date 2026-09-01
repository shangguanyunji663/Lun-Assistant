import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/* GitHub Pages 部署需要 base 指向 repo 路径（如 /Lun-Assistant/）。
   dev server 仍用 /（避免本地开发路径错乱）；build（NODE_ENV=production）切到 repo 路径。 */
const REPO_NAME = 'Lun-Assistant'

export default defineConfig({
  base: process.env.NODE_ENV === 'production' ? `/${REPO_NAME}/` : '/',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
