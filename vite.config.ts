import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => ({
  // Vercel serves from the domain root; GitHub Pages needs the repository prefix.
  base: mode === 'github-pages' ? '/scholarsaathi/' : '/',
  plugins: [react()],
}));
