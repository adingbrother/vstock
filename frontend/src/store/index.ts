// 导出所有store
export * from './taskStore'
export * from './appStore'

// 导入并导出所有store的具体实现
import { useTaskStore } from './taskStore'
import { useAppStore } from './appStore'

export {
  useTaskStore,
  useAppStore
}

// 初始化所有store的函数（可选择在应用启动时调用）
export function initializeStores() {
  const appStore = useAppStore()
  // 初始化应用状态
  appStore.initializeApp()
}