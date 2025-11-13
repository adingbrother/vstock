import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import { runFrontendTests } from './utils/testHelper'

// 创建应用实例
const app = createApp(App)

// 创建并使用Pinia
const pinia = createPinia()
app.use(pinia)

// 挂载应用
app.mount('#app')

// 应用启动后运行前端测试
try {
  // 在开发环境下运行测试
  if (import.meta.env.DEV) {
    console.log('初始化前端功能测试...')
    setTimeout(() => {
      runFrontendTests().then(result => {
        console.log('前端测试完成，结果:', result)
      }).catch(error => {
        console.error('测试运行失败:', error)
      })
    }, 1000) // 延迟执行，确保DOM已加载
  }
} catch (error) {
  console.error('测试初始化失败:', error)
}
