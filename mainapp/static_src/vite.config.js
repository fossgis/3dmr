import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  build: {
    publicDir: 'public',
    outDir: '../static/',
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, './src/main.js'),
      output: {
        entryFileNames: 'mainapp/[name].bundle.js',
      },
    },
  },
});
