// 策略相关API
import { request } from './service'

// 策略类型定义
export interface Strategy {
  id: number
  name: string
  description: string
  type: string
  return_rate: number
  risk_level: 'low' | 'medium' | 'high'
  status: '运行中' | '已停止' | '回测中' | '异常'
  created_at: string
  updated_at: string
  code?: string
  parameters?: Record<string, any>
}

// 策略查询参数
export interface StrategyQuery {
  page?: number
  page_size?: number
  status?: string
  type?: string
  risk_level?: string
  search?: string
}

// 策略分页响应
export interface StrategyListResponse {
  items: Strategy[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 策略API接口
export const strategyApi = {
  // 获取策略列表
  getStrategies: (query?: StrategyQuery) => {
    return request.get<StrategyListResponse>('/api/strategies', { params: query })
  },
  
  // 获取单个策略详情
  getStrategyById: (id: number) => {
    return request.get<Strategy>(`/api/strategies/${id}`)
  },
  
  // 创建策略
  createStrategy: (strategy: Omit<Strategy, 'id' | 'created_at' | 'updated_at'>) => {
    return request.post<Strategy>('/api/strategies', strategy)
  },
  
  // 更新策略
  updateStrategy: (id: number, strategy: Partial<Strategy>) => {
    return request.put<Strategy>(`/api/strategies/${id}`, strategy)
  },
  
  // 删除策略
  deleteStrategy: (id: number) => {
    return request.delete<{ success: boolean }>(`/api/strategies/${id}`)
  },
  
  // 启动策略
  startStrategy: (id: number) => {
    return request.post<{ success: boolean }>(`/api/strategies/${id}/start`)
  },
  
  // 停止策略
  stopStrategy: (id: number) => {
    return request.post<{ success: boolean }>(`/api/strategies/${id}/stop`)
  },
  
  // 获取策略运行历史
  getStrategyHistory: (id: number, limit?: number) => {
    return request.get<any[]>(`/api/strategies/${id}/history`, { params: { limit } })
  },
  
  // 克隆策略
  cloneStrategy: (id: number, newName: string) => {
    return request.post<Strategy>(`/api/strategies/${id}/clone`, { name: newName })
  },
  
  // 获取热门策略
  getPopularStrategies: (limit?: number) => {
    return request.get<Strategy[]>(`/api/strategies/popular`, { params: { limit } })
  }
}