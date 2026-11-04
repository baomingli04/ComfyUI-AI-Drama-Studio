import { defineConfig } from 'vite'
import vue2 from '@vitejs/plugin-vue2'

export default defineConfig({
  plugins: [vue2()],
  server: { port: 5199, host: '127.0.0.1', strictPort: true }
})
