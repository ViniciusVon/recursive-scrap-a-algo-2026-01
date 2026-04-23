import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

// Usamos `defineConfig` de `vitest/config` pra ganhar tipagem do campo
// `test` sem precisar de triple-slash reference. Em runtime, é o
// mesmo objeto consumido pelo Vite.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    // Exclui bundles de node_modules e artefatos do build; sem isso,
    // o vitest acha testes dentro do dist/ caso ele exista.
    exclude: ['node_modules', 'dist'],
  },
});
