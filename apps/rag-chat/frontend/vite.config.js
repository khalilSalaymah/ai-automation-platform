import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  root: '.',
  publicDir: 'public',
  plugins: [
    react({
      include: /\.(jsx|js)$/,
      jsxRuntime: 'automatic',
    }),
  ],
  resolve: {
    alias: {
      '@ui/components': path.resolve(__dirname, '../../../packages/ui/src'),
    },
  },
  esbuild: {
    include: /\.(jsx?|tsx?)$/,
    loader: 'jsx',
    jsxFactory: 'React.createElement',
    jsxFragment: 'React.Fragment',
  },
  optimizeDeps: {
    esbuildOptions: {
      loader: {
        '.js': 'jsx',
      },
    },
    include: [
      'react',
      'react-dom',
      'react-router-dom',
    ],
  },
  server: {
    host: '0.0.0.0',
    port: 3002,
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://localhost:8082',
        changeOrigin: true,
      },
    },
  },
})

