// ESLint 9 flat config（React + Vite）
import js from '@eslint/js'
import globals from 'globals'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'

export default [
  // scripts/ 为 Puppeteer 截图等开发辅助工具（浏览器注入环境），不纳入交付代码 lint
  { ignores: ['dist', 'node_modules', 'scripts'] },
  // 构建配置与脚本运行在 Node 环境（非浏览器）
  {
    files: ['vite.config.js', 'scripts/**/*.{js,mjs}'],
    languageOptions: { globals: globals.node },
    rules: { ...js.configs.recommended.rules, 'no-unused-vars': 'off' },
  },
  {
    files: ['**/*.{js,jsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: globals.browser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: {
      react,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    settings: { react: { version: 'detect' } },
    rules: {
      ...js.configs.recommended.rules,
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      // React 17+ 自动 JSX transform：无需显式 import React 到作用域
      'react/react-in-jsx-scope': 'off',
      // 组件 props 已用 TS/文档约定约束，不强制 prop-types
      'react/prop-types': 'off',
      // React 18 常见的数据加载/初始化模式（effect 内同步 setState 属正常，
      // 该规则面向 React 19 compiler 迁移，暂不启用）
      'react-hooks/set-state-in-effect': 'off',
      // 允许未使用的大写标识（如 JSX 组件 import、React 命名空间）
      'no-unused-vars': ['error', { varsIgnorePattern: '^[A-Z_]' }],
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    },
  },
]
