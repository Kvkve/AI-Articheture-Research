import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// The address of the backend that the development server passes calls on
// to. The default is the address that uvicorn uses when given none.
const backendAddress = process.env.POC_BACKEND_ADDRESS ?? 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // The page calls its own address under /api, so the browser needs no
      // permission to call another address. This rule passes such a call on
      // to the backend with the prefix taken off: /api/conversations becomes
      // /conversations. The same prefix is API_PREFIX in
      // frontend/src/backend.ts.
      '/api': {
        target: backendAddress,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  test: {
    // Components need a browser-like page to render into.
    environment: 'jsdom',
  },
})
