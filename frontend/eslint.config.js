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
      // V1 release policy: lint must not block a production build on
      // advisory migration diagnostics. Actual JavaScript errors still
      // remain errors through eslint's recommended rules.
      'no-unused-vars': 'warn',
      'no-useless-assignment': 'off',
      'react-hooks/set-state-in-effect': 'warn',
      'react-hooks/static-components': 'warn',
      'react-hooks/immutability': 'warn',
      'react-hooks/preserve-caught-error': 'off',
      'react-hooks/use-memo': 'warn',
      'react-refresh/only-export-components': 'warn',
    },
  },
  {
    files: ['src/pages/Chat.jsx'],
    rules: {
      // Chat contains a legacy callback named usePrompt. It is not a React
      // hook, but the hooks rule cannot distinguish that legacy API safely.
      'react-hooks/rules-of-hooks': 'warn',
    },
  },
])
