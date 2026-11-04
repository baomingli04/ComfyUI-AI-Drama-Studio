import { defineConfig } from 'vite'
import vue2 from '@vitejs/plugin-vue2'
import { fileURLToPath } from 'url'

export default defineConfig({
  plugins: [vue2()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    // 8080 属于 llama-server，前端固定用 8081，避免抢占
    port: 8081,
    strictPort: true,
    host: '0.0.0.0'
  }
})
