import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import type { Task, TaskParameters, TaskResult } from '../types/task'

// API响应基础接口
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  success: boolean
}

// 分页响应接口
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 策略信息接口
export interface StrategyInfo {
  id: string
  name: string
  description: string
  code: string
  parameters_schema: Record<string, any>
  created_at: string
  updated_at: string
}

// 策略实例接口
export interface StrategyInstance {
  id: string
  strategy_id: string
  name: string
  parameters: Record<string, any>
  created_at: string
  updated_at: string
}

// 推荐结果接口
export interface RecommendResult {
  task_id: string
  trading_date: string
  rank: number
  stock_code: string
  stock_name: string
  score: number
  factors: Record<string, number>
  created_at: string
}

// 因子配置接口
export interface FactorConfig {
  factor_name: string
  weight: number
  enabled: boolean
  description?: string
}

// 数据源信息接口
export interface DataSourceInfo {
  source_id: string
  name: string
  description: string
  supported_data_types: string[]
  is_active: boolean
}

// 下载请求接口
export interface DownloadRequest {
  source: string
  stock_codes: string[]
  data_type: string
  start_date: string
  end_date: string
  adjust_type?: 'None' | 'Forward' | 'Backward'
}

// API服务类
class ApiService {
  private axios: AxiosInstance
  private baseURL: string
  private retryCount = 0
  private maxRetryCount = 3
  private retryDelay = 1000

  constructor() {
    // 从环境变量读取API基础URL，如果没有则使用默认值
    this.baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

    // 创建axios实例
    this.axios = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // 请求拦截器
    this.axios.interceptors.request.use(
      (config) => {
        // 可以在这里添加认证token等
        const token = localStorage.getItem('token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // 响应拦截器
    this.axios.interceptors.response.use(
      (response) => {
        return response
      },
      async (error) => {
        const originalRequest = error.config

        // 重试机制
        if (!originalRequest._retry && this.retryCount < this.maxRetryCount) {
          originalRequest._retry = true
          this.retryCount++
          
          await new Promise((resolve) => setTimeout(resolve, this.retryDelay * this.retryCount))
          return this.axios(originalRequest)
        }

        // 错误处理
        const errorMessage = this.handleApiError(error)
        ElMessage.error(errorMessage)
        
        this.retryCount = 0 // 重置重试计数
        return Promise.reject(error)
      }
    )
  }

  // 处理API错误
  private handleApiError(error: any): string {
    if (error.response) {
      // 服务器响应了但状态码不是2xx
      const { status, data } = error.response
      
      switch (status) {
        case 400:
          return data.message || '请求参数错误'
        case 401:
          return '未授权，请重新登录'
        case 403:
          return '拒绝访问'
        case 404:
          return '请求的资源不存在'
        case 500:
          return data.message || '服务器内部错误'
        default:
          return `请求失败: ${status}`
      }
    } else if (error.request) {
      // 请求已发出但没有收到响应
      return '网络错误，请检查您的网络连接'
    } else {
      // 请求配置出错
      return error.message || '请求错误'
    }
  }

  // 通用请求方法
  private async request<T>(config: AxiosRequestConfig): Promise<T> {
    try {
      const response: AxiosResponse<ApiResponse<T>> = await this.axios(config)
      
      if (response.data.success) {
        return response.data.data
      } else {
        ElMessage.error(response.data.message)
        throw new Error(response.data.message)
      }
    } catch (error) {
      throw error
    }
  }

  // 策略管理API
  public strategy = {
    // 获取策略列表
    getStrategies: async (): Promise<StrategyInfo[]> => {
      return this.request<StrategyInfo[]>({
        method: 'GET',
        url: '/strategy/list',
      })
    },

    // 获取策略详情
    getStrategy: async (strategyId: string): Promise<StrategyInfo> => {
      return this.request<StrategyInfo>({
        method: 'GET',
        url: `/strategy/${strategyId}`,
      })
    },

    // 获取策略实例列表
    getInstances: async (): Promise<StrategyInstance[]> => {
      return this.request<StrategyInstance[]>({
        method: 'GET',
        url: '/strategy/instances',
      })
    },

    // 创建策略实例
    createInstance: async (data: { strategy_id: string; name: string; parameters: Record<string, any> }): Promise<StrategyInstance> => {
      return this.request<StrategyInstance>({
        method: 'POST',
        url: '/strategy/instance',
        data,
      })
    },

    // 获取策略实例详情
    getInstance: async (instanceId: string): Promise<StrategyInstance> => {
      return this.request<StrategyInstance>({
        method: 'GET',
        url: `/strategy/instance/${instanceId}`,
      })
    },

    // 更新策略实例
    updateInstance: async (instanceId: string, data: { name?: string; parameters?: Record<string, any> }): Promise<StrategyInstance> => {
      return this.request<StrategyInstance>({
        method: 'PUT',
        url: `/strategy/instance/${instanceId}`,
        data,
      })
    },

    // 删除策略实例
    deleteInstance: async (instanceId: string): Promise<void> => {
      return this.request<void>({
        method: 'DELETE',
        url: `/strategy/instance/${instanceId}`,
      })
    },
  }

  // 推荐引擎API
  public recommend = {
    // 创建推荐任务
    createTask: async (data: { stock_pool: string[]; date?: string; factor_weights?: Record<string, number> }): Promise<{ task_id: string }> => {
      return this.request<{ task_id: string }>({
        method: 'POST',
        url: '/recommend',
        data,
      })
    },

    // 获取任务状态
    getTaskStatus: async (taskId: string): Promise<{ status: string; progress: number }> => {
      return this.request<{ status: string; progress: number }>({
        method: 'GET',
        url: `/recommend/status/${taskId}`,
      })
    },

    // 获取推荐结果
    getResults: async (taskId: string): Promise<RecommendResult[]> => {
      return this.request<RecommendResult[]>({
        method: 'GET',
        url: `/recommend/result/${taskId}`,
      })
    },

    // 获取因子配置
    getFactorConfig: async (): Promise<FactorConfig[]> => {
      return this.request<FactorConfig[]>({
        method: 'GET',
        url: '/recommend/factors',
      })
    },

    // 更新因子配置
    updateFactorConfig: async (factors: FactorConfig[]): Promise<FactorConfig[]> => {
      return this.request<FactorConfig[]>({
        method: 'PUT',
        url: '/recommend/factors',
        data: { factors },
      })
    },

    // 获取推荐历史
    getHistory: async (params?: { page?: number; pageSize?: number; date?: string }): Promise<PaginatedResponse<RecommendResult>> => {
      return this.request<PaginatedResponse<RecommendResult>>({
        method: 'GET',
        url: '/recommend/history',
        params,
      })
    },
  }

  // 数据管理API
  public data = {
    // 获取数据源列表
    getDataSources: async (): Promise<DataSourceInfo[]> => {
      return this.request<DataSourceInfo[]>({
        method: 'GET',
        url: '/data/sources',
      })
    },

    // 获取已下载股票列表
    getDownloadedStocks: async (params?: { source?: string; data_type?: string }): Promise<{ stock_code: string; stock_name: string; downloaded_at: string }[]> => {
      return this.request<{ stock_code: string; stock_name: string; downloaded_at: string }[]>({
        method: 'GET',
        url: '/data/stocks',
        params,
      })
    },

    // 下载数据
    download: async (request: DownloadRequest): Promise<{ task_id: string; estimated_time: number }> => {
      return this.request<{ task_id: string; estimated_time: number }>({
        method: 'POST',
        url: '/data/download',
        data: request,
      })
    },

    // 查询股票数据
    queryStockData: async (params: { stock_code: string; start_date: string; end_date: string; data_type: string }): Promise<any[]> => {
      return this.request<any[]>({
        method: 'GET',
        url: '/data/query',
        params,
      })
    },

    // 清理缓存
    clearCache: async (): Promise<void> => {
      return this.request<void>({
        method: 'DELETE',
        url: '/data/cache',
      })
    },

    // 获取数据统计
    getStatistics: async (): Promise<{ total_stocks: number; total_records: number; cache_size: string; last_update: string }> => {
      return this.request<{ total_stocks: number; total_records: number; cache_size: string; last_update: string }>({
        method: 'GET',
        url: '/data/stats',
      })
    },

    // 验证数据完整性
    verifyData: async (stock_codes: string[], data_type: string): Promise<{ valid: string[]; missing: string[]; corrupted: string[] }> => {
      return this.request<{ valid: string[]; missing: string[]; corrupted: string[] }>({
        method: 'POST',
        url: '/data/verify',
        data: { stock_codes, data_type },
      })
    },
  }

  // 回测API
  public backtest = {
    // 提交回测任务
    submit: async (data: {
      strategy_config: {
        name: string;
        parameters: Record<string, any>;
      };
      stock_code: string;
      start_date: string;
      end_date: string;
      initial_capital?: number;
    }): Promise<{ task_id: string }> => {
      return this.request<{ task_id: string }>({
        method: 'POST',
        url: '/backtest/submit',
        data,
      })
    },

    // 获取回测任务状态
    getStatus: async (taskId: string): Promise<{ status: string; progress: number }> => {
      return this.request<{ status: string; progress: number }>({
        method: 'GET',
        url: `/backtest/status/${taskId}`,
      })
    },

    // 获取回测结果
    getResult: async (taskId: string): Promise<TaskResult> => {
      return this.request<TaskResult>({
        method: 'GET',
        url: `/backtest/result/${taskId}`,
      })
    },
  }

  // 任务管理API
  public task = {
    // 获取任务列表
    getTasks: async (params?: {
      page?: number;
      pageSize?: number;
      type?: string;
      status?: string;
    }): Promise<PaginatedResponse<Task>> => {
      return this.request<PaginatedResponse<Task>>({n        method: 'GET',
        url: '/tasks',
        params,
      })
    },

    // 获取任务详情
    getTask: async (taskId: string): Promise<Task> => {
      return this.request<Task>({
        method: 'GET',
        url: `/tasks/${taskId}`,
      })
    },

    // 取消任务
    cancelTask: async (taskId: string): Promise<void> => {
      return this.request<void>({
        method: 'POST',
        url: `/tasks/${taskId}/cancel`,
      })
    },

    // 删除任务
    deleteTask: async (taskId: string): Promise<void> => {
      return this.request<void>({
        method: 'DELETE',
        url: `/tasks/${taskId}`,
      })
    },
  }

  // 批量请求处理
  public batch = {
    // 并行执行多个请求
    parallel: async <T extends any[]>(requests: (() => Promise<any>)[]): Promise<T> => {
      try {
        const results = await Promise.all(requests)
        return results as T
      } catch (error) {
        ElMessage.error('批量请求执行失败')
        throw error
      }
    },

    // 串行执行多个请求
    series: async <T extends any[]>(requests: (() => Promise<any>)[]): Promise<T> => {
      const results: any[] = []
      
      try {
        for (const request of requests) {
          const result = await request()
          results.push(result)
        }
        return results as T
      } catch (error) {
        ElMessage.error('串行请求执行失败')
        throw error
      }
    },
  }

  // 导出数据
  public export = {
    // 导出数据为CSV
    toCsv: async (url: string, params?: any): Promise<string> => {
      const response = await this.axios({
        method: 'GET',
        url,
        params,
        responseType: 'blob',
      })
      
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = (e) => {
          if (e.target?.result) {
            resolve(e.target.result as string)
          } else {
            reject(new Error('无法读取CSV数据'))
          }
        }
        reader.onerror = () => reject(new Error('读取CSV失败'))
        reader.readAsText(response.data)
      })
    },

    // 下载文件
    downloadFile: async (url: string, filename?: string): Promise<void> => {
      const response = await this.axios({
        method: 'GET',
        url,
        responseType: 'blob',
      })
      
      // 创建下载链接
      const blob = new Blob([response.data])
      const link = document.createElement('a')
      link.href = window.URL.createObjectURL(blob)
      
      // 设置文件名
      link.download = filename || this.getFilenameFromResponse(response)
      
      // 模拟点击下载
      document.body.appendChild(link)
      link.click()
      
      // 清理
      setTimeout(() => {
        document.body.removeChild(link)
        window.URL.revokeObjectURL(link.href)
      }, 100)
    },

    // 从响应头获取文件名
    private getFilenameFromResponse(response: AxiosResponse): string {
      const contentDisposition = response.headers['content-disposition']
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/)
        if (match && match[1]) {
          return match[1]
        }
      }
      return 'download.dat'
    },
  }
}

// 导出API服务单例
export const apiService = new ApiService()

// 导出Vue组合式函数
export function useApi() {
  return {
    api: apiService,
    strategy: apiService.strategy,
    recommend: apiService.recommend,
    data: apiService.data,
    backtest: apiService.backtest,
    task: apiService.task,
    batch: apiService.batch,
    export: apiService.export,
  }
}
