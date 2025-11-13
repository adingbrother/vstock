// 回测相关API
import { request } from './service'

// 回测参数
export interface BacktestParams {
  strategy_id?: number
  strategy_name?: string
  strategy_code?: string
  initial_capital: number
  start_date: string
  end_date: string
  symbols: string[]
  parameters?: Record<string, any>
  risk_level?: 'low' | 'medium' | 'high'
}

// 回测结果
export interface BacktestResult {
  id: string
  strategy_id?: number
  strategy_name: string
  initial_capital: number
  final_capital: number
  total_return: number
  annual_return: number
  sharpe_ratio: number
  max_drawdown: number
  win_rate: number
  trade_count: number
  start_date: string
  end_date: string
  status: 'completed' | 'running' | 'failed'
  created_at: string
  completed_at?: string
  equity_curve?: Array<{ date: string; value: number }>
  trades?: Array<{
    id: number
    symbol: string
    entry_date: string
    exit_date?: string
    entry_price: number
    exit_price?: number
    quantity: number
    status: 'open' | 'closed'
    profit?: number
    profit_percent?: number
  }>
  error?: string
}

// 回测任务
export interface BacktestTask {
  id: string
  name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  created_at: string
  started_at?: string
  completed_at?: string
}

// 回测API接口
export const backtestApi = {
  // 提交回测任务
  submitBacktest: (params: BacktestParams) => {
    return request.post<{ task_id: string }>('/api/backtest', params)
  },
  
  // 获取回测任务状态
  getBacktestStatus: (taskId: string) => {
    return request.get<BacktestTask>(`/api/backtest/status/${taskId}`)
  },
  
  // 获取回测结果
  getBacktestResult: (taskId: string) => {
    return request.get<BacktestResult>(`/api/backtest/result/${taskId}`)
  },
  
  // 获取回测任务列表
  getBacktestTasks: (query?: { status?: string; page?: number; page_size?: number }) => {
    return request.get<{ items: BacktestTask[]; total: number }>('/api/backtest/tasks', { params: query })
  },
  
  // 取消回测任务
  cancelBacktest: (taskId: string) => {
    return request.post<{ success: boolean }>(`/api/backtest/cancel/${taskId}`)
  },
  
  // 删除回测结果
  deleteBacktestResult: (resultId: string) => {
    return request.delete<{ success: boolean }>(`/api/backtest/result/${resultId}`)
  },
  
  // 获取回测性能指标
  getBacktestMetrics: (resultId: string) => {
    return request.get<{
      total_return: number
      annual_return: number
      sharpe_ratio: number
      sortino_ratio: number
      max_drawdown: number
      calmar_ratio: number
      win_rate: number
      profit_factor: number
      alpha: number
      beta: number
      r_squared: number
    }>(`/api/backtest/metrics/${resultId}`)
  },
  
  // 对比多个回测结果
  compareBacktests: (resultIds: string[]) => {
    return request.post<{
      results: BacktestResult[]
      comparison: Record<string, any>
    }>('/api/backtest/compare', { result_ids: resultIds })
  },
  
  // 获取回测交易记录
  getBacktestTrades: (resultId: string, query?: { page?: number; page_size?: number }) => {
    return request.get<{
      items: Array<{
        id: number
        symbol: string
        entry_date: string
        exit_date?: string
        entry_price: number
        exit_price?: number
        quantity: number
        status: 'open' | 'closed'
        profit?: number
        profit_percent?: number
      }>
      total: number
    }>(`/api/backtest/trades/${resultId}`, { params: query })
  }
}