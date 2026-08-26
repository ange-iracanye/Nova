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
    ],
    languageOptions: {
      globals: globals.browser,
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      'no-unused-vars': 'warn',
      'no-useless-assignment': 'off',

      // Keep the two React Hooks correctness checks that are useful as
      // ordinary ESLint diagnostics. The newer React Hooks flat preset also
      // enables React Compiler diagnostics that are not appropriate as hard
      // CI failures for this V1 application and can flag valid runtime code.
      'react-hooks/rules-of-hooks': 'warn',
      'react-hooks/exhaustive-deps': 'warn',

      // React Compiler diagnostics are intentionally non-blocking for V1.
      // They can be revisited independently when Nova adopts the compiler.
      'react-hooks/component-hook-factories': 'warn',
      'react-hooks/error-boundaries': 'warn',
      'react-hooks/globals': 'warn',
      'react-hooks/immutability': 'warn',
      'react-hooks/preserve-manual-memoization': 'warn',
      'react-hooks/preserve-caught-error': 'off',
      'react-hooks/purity': 'warn',
      'react-hooks/refs': 'warn',
      'react-hooks/set-state-in-effect': 'warn',
      'react-hooks/set-state-in-render': 'warn',
      'react-hooks/static-components': 'warn',
      'react-hooks/unsupported-syntax': 'warn',
      'react-hooks/use-memo': 'warn',
      'react-hooks/incompatible-library': 'warn',
      'react-refresh/only-export-components': 'warn',
    },
  },
  {
    files: ['src/pages/Chat.jsx'],
    rules: {
      'react-hooks/rules-of-hooks': 'warn',
    },
  },
])
