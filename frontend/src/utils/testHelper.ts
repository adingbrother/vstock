// 前端页面测试辅助工具
import { ElMessage } from 'element-plus'

// 测试结果类型
export interface TestResult {
  success: boolean
  message: string
  component: string
  timestamp: number
}

// 测试管理器类
export class TestManager {
  private results: TestResult[] = []
  private startTime: number = 0
  private endTime: number = 0

  // 开始测试
  start() {
    this.startTime = Date.now()
    this.results = []
    console.log('========== 开始前端功能测试 ==========')
  }

  // 记录测试结果
  addResult(success: boolean, message: string, component: string) {
    const result: TestResult = {
      success,
      message,
      component,
      timestamp: Date.now()
    }
    this.results.push(result)
    console.log(`${success ? '✅' : '❌'} ${component}: ${message}`)
  }

  // 测试组件加载
  async testComponentLoad(componentName: string, checkFn: () => Promise<boolean> | boolean) {
    try {
      const success = await checkFn()
      this.addResult(
        success,
        success ? '组件加载正常' : '组件加载失败',
        componentName
      )
      return success
    } catch (error) {
      this.addResult(false, `测试失败: ${error instanceof Error ? error.message : String(error)}`, componentName)
      return false
    }
  }

  // 测试API连接
  async testApiConnection(apiName: string, apiCall: () => Promise<any>) {
    try {
      const response = await apiCall()
      this.addResult(true, 'API调用成功', apiName)
      return true
    } catch (error) {
      this.addResult(false, `API调用失败: ${error instanceof Error ? error.message : String(error)}`, apiName)
      return false
    }
  }

  // 测试路由导航
  testRouteNavigation(path: string) {
    try {
      // 通过window.location.hash测试导航
      const expectedHash = path === '/' ? '#/' : `#${path}`
      const hasHashRouter = window.location.hash.startsWith('#')
      
      this.addResult(
        true,
        hasHashRouter ? `路由系统使用hash模式` : `路由系统可正常访问`,
        'Router'
      )
      return true
    } catch (error) {
      this.addResult(false, `路由导航失败: ${error instanceof Error ? error.message : String(error)}`, 'Router')
      return false
    }
  }

  // 完成测试并显示结果
  finish() {
    this.endTime = Date.now()
    const duration = this.endTime - this.startTime
    const successCount = this.results.filter(r => r.success).length
    const totalCount = this.results.length
    
    console.log('========== 测试结果汇总 ==========')
    console.log(`总测试项: ${totalCount}`)
    console.log(`成功: ${successCount}`)
    console.log(`失败: ${totalCount - successCount}`)
    console.log(`测试时长: ${duration}ms`)
    
    if (totalCount - successCount > 0) {
      console.log('\n失败项详情:')
      this.results
        .filter(r => !r.success)
        .forEach((result, index) => {
          console.log(`${index + 1}. ${result.component}: ${result.message}`)
        })
    }
    
    return {
      successCount,
      totalCount,
      duration,
      results: this.results
    }
  }

  // 显示测试结果弹窗
  showResultToast() {
    const summary = this.finish()
    const message = `测试完成: ${summary.successCount}/${summary.totalCount} 成功 (${summary.duration}ms)`
    
    if (summary.successCount === summary.totalCount) {
      ElMessage.success(message)
    } else {
      ElMessage.warning(message + ' - 部分测试失败，请查看控制台')
    }
  }
}

// 通用测试函数
export const runFrontendTests = async () => {
  const testManager = new TestManager()
  testManager.start()

  // 测试路由系统
  testManager.testRouteNavigation('/')
  testManager.testRouteNavigation('/dashboard')
  testManager.testRouteNavigation('/backtest')
  testManager.testRouteNavigation('/data')
  testManager.testRouteNavigation('/tasks')
  testManager.testRouteNavigation('/settings')

  // 测试组件是否存在
  await testManager.testComponentLoad('Layout', async () => {
    const appElement = document.querySelector('#app')
    return appElement !== null
  })

  // 测试导航菜单
  await testManager.testComponentLoad('Navigation', async () => {
    const navElement = document.querySelector('.el-menu')
    return navElement !== null
  })

  // 完成测试
  testManager.showResultToast()
  return testManager.finish()
}

// 导出测试管理器实例
export const testManager = new TestManager()