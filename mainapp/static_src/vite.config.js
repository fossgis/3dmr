import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  build: {
    publicDir: 'public',
    outDir: '../static/mainapp',
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, './src/main.js'),
      output: {
        entryFileNames: '[name].bundle.js',
      },
    },
  },
});
