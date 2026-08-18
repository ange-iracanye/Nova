import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    rules: {
      // Nova is currently migrating a large pre-React-Compiler codebase.
      // Keep these diagnostics visible without blocking production builds.
      'no-unused-vars': 'warn',
      'react-hooks/set-state-in-effect': 'warn',
      'react-hooks/static-components': 'warn',
      'react-hooks/immutability': 'warn',
      'react-hooks/preserve-caught-error': 'warn',
      'react-hooks/use-memo': 'warn',
      'react-refresh/only-export-components': 'warn',
    },
  },
  {
    files: ['src/pages/Chat.jsx'],
    rules: {
      // Chat is a deliberately frozen V1 UI. Its legacy callback naming
      // triggers the hooks rule even though the underlying function is not
      // a React hook. Keep it visible as a warning until the Chat refactor.
      'react-hooks/rules-of-hooks': 'warn',
    },
  },
])
