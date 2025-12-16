import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  base: '/static/',
  build: {
    publicDir: 'public',
    outDir: resolve(__dirname, '../static/'),
    manifest: 'mainapp/manifest.json',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'src/main.js'),
      },
      output: {
        entryFileNames: 'mainapp/[name].bundle.js',
      },
    },
  },
});
