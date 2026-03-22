import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { viteStaticCopy } from 'vite-plugin-static-copy';

export default defineConfig({
  plugins: [
    react(),
    viteStaticCopy({
      targets: [
        { src: 'src/plugin.json', dest: '.' },
        { src: 'src/img', dest: 'img' },
      ],
    }),
  ],
  build: {
    rollupOptions: {
      input: 'src/module.tsx',
      preserveEntrySignatures: 'exports-only',
      output: {
        format: 'amd',
        entryFileNames: 'module.js',
      },
      external: [
        'react',
        'react-dom',
        'lodash',
        '@grafana/data',
        '@grafana/ui',
        '@grafana/runtime',
      ],
    },
    target: 'es2022',
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true,
  },
});
