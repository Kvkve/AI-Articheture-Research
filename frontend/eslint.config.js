import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
    },
  },
  {
    // Only src/backend.ts talks to the backend, so that the code of the
    // network stays in one module, apart from the components. The same idea
    // as the rule in backend/pyproject.toml that only app/agent.py imports
    // the SDK.
    files: ['src/**/*.{ts,tsx}'],
    ignores: ['src/backend.ts'],
    rules: {
      'no-restricted-globals': [
        'error',
        { name: 'fetch', message: 'Only src/backend.ts may call fetch. Call a function of that module.' },
      ],
      'no-restricted-properties': [
        'error',
        { object: 'window', property: 'fetch', message: 'Only src/backend.ts may call fetch.' },
        { object: 'globalThis', property: 'fetch', message: 'Only src/backend.ts may call fetch.' },
      ],
    },
  },
])
