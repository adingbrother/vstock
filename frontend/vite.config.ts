import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    mcpServers: {
      'git-service': {
        command: '/usr/local/bin/git',
        args: [
          'daemon',
          '--reuseaddr',
          '--base-path=/Users/wangxx/Desktop/python3/vstock',
          '--export-all',
          '--verbose'
        ]
      },
      'mcp-agent': {
        command: 'node',
        args: [
          '--inspect',
          '/path/to/mcp/agent.js'
        ],
        env: {
          'MCP_AGENT_PORT': '8080',
          'MCP_AGENT_NAME': 'vstock-agent',
          'MCP_AGENT_TYPE': 'quant'
        }
      }
    }
  },
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: [],
    include: ['**/*.test.ts'],
    exclude: ['node_modules', 'dist'],
    coverage: {
      reporter: ['text', 'json', 'html']
    }
  }
})
