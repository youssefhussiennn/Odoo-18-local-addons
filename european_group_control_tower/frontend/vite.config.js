import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Builds the whole app (React + SheetJS + CSS + logo) into ONE self-contained IIFE file that the Odoo
// client action loads lazily and mounts through `window.EGControlTower.mount(el, { rpc })`.
export default defineConfig({
  plugins: [react()],
  define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  server: { port: 5173, open: false },
  build: {
    outDir: '../static/dist',
    emptyOutDir: true,
    sourcemap: false,
    cssCodeSplit: false,
    assetsInlineLimit: 10_000_000,
    lib: {
      entry: 'src/main.jsx',
      name: 'EGControlTower',
      formats: ['iife'],
      fileName: () => 'egct.iife.js',
    },
    rollupOptions: { output: { inlineDynamicImports: true } },
  },
});
