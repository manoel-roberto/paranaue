import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// Configuração do Vite para o frontend Vue 3
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  server: {
    port: 5173,
  },
});
