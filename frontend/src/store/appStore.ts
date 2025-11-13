import { defineStore } from 'pinia'

// 用户信息接口
interface User {
  id: number | null
  username: string | null
  email: string | null
  role: string | null
}

// 系统配置接口
interface SystemConfig {
  apiBaseUrl: string
  websocketUrl: string
  autoRefreshInterval: number
  maxTasksDisplay: number
}

// 应用状态接口
interface AppState {
  user: User
  isLoggedIn: boolean
  sidebarCollapsed: boolean
  theme: 'light' | 'dark'
  loading: boolean
  error: string | null
  success: string | null
  config: SystemConfig
}

export const useAppStore = defineStore('app', {
  state: (): AppState => ({
    user: {
      id: null,
      username: null,
      email: null,
      role: null
    },
    isLoggedIn: false,
    sidebarCollapsed: false,
    theme: 'light',
    loading: false,
    error: null,
    success: null,
    config: {
      apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api',
      websocketUrl: import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws',
      autoRefreshInterval: 5000, // 5秒
      maxTasksDisplay: 50
    }
  }),

  getters: {
    // 获取显示名称
    displayName(): string {
      return this.user.username || '未登录用户'
    },

    // 检查是否有管理员权限
    isAdmin(): boolean {
      return this.user.role === 'ADMIN'
    },

    // 获取当前主题类名
    themeClass(): string {
      return this.theme === 'dark' ? 'dark-theme' : 'light-theme'
    }
  },

  actions: {
    // 设置用户信息
    setUser(user: User) {
      this.user = user
      this.isLoggedIn = true
      // 将用户信息保存到本地存储
      localStorage.setItem('user', JSON.stringify(user))
    },

    // 清除用户信息（登出）
    clearUser() {
      this.user = {
        id: null,
        username: null,
        email: null,
        role: null
      }
      this.isLoggedIn = false
      // 从本地存储移除用户信息
      localStorage.removeItem('user')
    },

    // 从本地存储恢复用户信息
    restoreUser() {
      const savedUser = localStorage.getItem('user')
      if (savedUser) {
        try {
          this.setUser(JSON.parse(savedUser))
        } catch (error) {
          console.error('恢复用户信息失败:', error)
          localStorage.removeItem('user')
        }
      }
    },

    // 切换侧边栏状态
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },

    // 设置侧边栏状态
    setSidebarCollapsed(collapsed: boolean) {
      this.sidebarCollapsed = collapsed
    },

    // 切换主题
    toggleTheme() {
      this.theme = this.theme === 'light' ? 'dark' : 'light'
      this.applyTheme()
    },

    // 设置主题
    setTheme(theme: 'light' | 'dark') {
      this.theme = theme
      this.applyTheme()
    },

    // 应用主题到DOM
    applyTheme() {
      document.documentElement.classList.toggle('dark', this.theme === 'dark')
      localStorage.setItem('theme', this.theme)
    },

    // 从本地存储恢复主题
    restoreTheme() {
      const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null
      if (savedTheme) {
        this.setTheme(savedTheme)
      }
    },

    // 设置加载状态
    setLoading(loading: boolean) {
      this.loading = loading
    },

    // 设置错误消息
    setError(message: string | null) {
      this.error = message
      // 3秒后自动清除错误消息
      if (message) {
        setTimeout(() => {
          this.error = null
        }, 3000)
      }
    },

    // 设置成功消息
    setSuccess(message: string | null) {
      this.success = message
      // 3秒后自动清除成功消息
      if (message) {
        setTimeout(() => {
          this.success = null
        }, 3000)
      }
    },

    // 更新配置
    updateConfig(config: Partial<SystemConfig>) {
      this.config = { ...this.config, ...config }
    },

    // 初始化应用状态
    initializeApp() {
      this.restoreTheme()
      this.restoreUser()
    }
  }
})