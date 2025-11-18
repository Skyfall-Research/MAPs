import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  root: 'map_js/gui',
  server: {
    port: 3001,
    open: true
  },
  resolve: {
    alias: {
      '@shared': path.resolve(__dirname, 'shared')
    }
  },
  publicDir: path.resolve(__dirname, 'shared')
});