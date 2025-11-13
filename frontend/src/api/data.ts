// 数据相关API
import { request } from './service'

// 数据下载参数
export interface DataDownloadParams {
  symbols: string[]
  data_type: 'stock' | 'index' | 'fund' | 'future'
  start_date: string
  end_date: string
  fields?: string[]
  frequency?: 'daily' | 'weekly' | 'monthly' | 'minute'
}

// 数据文件信息
export interface DataFile {
  id: string
  filename: string
  file_size: number
  file_type: string
  upload_time: string
  download_url: string
  status: 'completed' | 'processing' | 'failed'
  progress?: number
  type: 'stock' | 'index' | 'fund' | 'future' | 'other'
}

// 数据API接口
export const dataApi = {
  // 下载股票数据
  downloadStockData: (params: DataDownloadParams) => {
    return request.post<{ task_id: string }>('/api/data/download', params)
  },
  
  // 获取数据文件列表
  getDataFiles: (query?: { type?: string; status?: string; page?: number; page_size?: number }) => {
    return request.get<{ items: DataFile[]; total: number }>('/api/data/files', { params: query })
  },
  
  // 获取单个数据文件详情
  getDataFile: (id: string) => {
    return request.get<DataFile>(`/api/data/files/${id}`)
  },
  
  // 删除数据文件
  deleteDataFile: (id: string) => {
    return request.delete<{ success: boolean }>(`/api/data/files/${id}`)
  },
  
  // 上传数据文件
  uploadDataFile: (formData: FormData) => {
    return request.post<DataFile>('/api/data/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  
  // 检查数据下载任务状态
  checkDownloadStatus: (taskId: string) => {
    return request.get<{ status: string; progress: number; download_url?: string }>(
      `/api/data/download/status/${taskId}`
    )
  },
  
  // 获取支持的数据字段
  getDataFields: (dataType?: string) => {
    return request.get<string[]>(`/api/data/fields`, { params: { data_type: dataType } })
  },
  
  // 获取市场行情快照
  getMarketSnapshot: () => {
    return request.get<Array<{
      symbol: string
      name: string
      price: number
      change: number
      change_percent: number
      volume: number
    }>>('/api/data/market/snapshot')
  },
  
  // 批量获取股票基本信息
  getStockInfo: (symbols: string[]) => {
    return request.get<any[]>(`/api/data/stocks/info`, { params: { symbols: symbols.join(',') } })
  }
}