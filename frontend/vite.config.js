import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/* GitHub Pages 部署需要 base 指向 repo 路径（如 /Lun-Assistant/）。
   dev server 仍用 /（避免本地开发路径错乱）；build（NODE_ENV=production）切到 repo 路径。 */
const REPO_NAME = 'Lun-Assistant'

/* v18 多入口：站根落地页（皮肤 A）+ 工作台 + 其余五套皮肤的落地页。
   六套设计语言的版式差异过大，无法靠 CSS 换肤，故落地页每套一个 HTML；
   工作台是同一个 React SPA，靠 <html data-skin> 换肤（见 src/skins/）。 */
const page = (name) => fileURLToPath(new URL(`./${name}`, import.meta.url))

export default defineConfig({
  base: process.env.NODE_ENV === 'production' ? `/${REPO_NAME}/` : '/',
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        index: page('index.html'),
        app: page('app.html'),
        'landing-b': page('landing-b.html'),
        'landing-c': page('landing-c.html'),
        'landing-d': page('landing-d.html'),
        'landing-e': page('landing-e.html'),
        'landing-f': page('landing-f.html'),
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
