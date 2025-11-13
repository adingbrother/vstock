import { defineStore } from 'pinia'
import axios from 'axios'
import type { Task } from '../types/task'
import { wsService, type TaskStatusUpdate } from '../services/websocketService'

// 定义任务状态接口
export interface TaskState {
  tasks: Task[]
  selectedTask: Task | null
  selectedTaskIds: string[] // 用于批量操作的选中任务ID列表
  loading: boolean
  loadingMore: boolean // 用于标识是否正在加载更多数据（虚拟滚动）
  hasMoreTasks: boolean // 用于标识是否还有更多任务可以加载
  currentPage: number // 当前页码
  pageSize: number // 每页任务数量
  error: string | null
  filters: {
    keyword: string
    type: string
    status: string
    dateRange: [string, string] | []
  }
}

export const useTaskStore = defineStore('task', {
  state: (): TaskState => ({
    tasks: [],
    selectedTask: null,
    selectedTaskIds: [], // 初始化选中任务ID列表为空
    loading: false,
    loadingMore: false,
    hasMoreTasks: true,
    currentPage: 1,
    pageSize: 50,
    error: null,
    filters: {
      keyword: '',
      type: '',
      status: '',
      dateRange: []
    }
  }),

  getters: {
    // 获取过滤后的任务列表
    filteredTasks(): Task[] {
      let filtered = [...this.tasks]
      
      // 关键词过滤
      if (this.filters.keyword) {
        const keyword = this.filters.keyword.toLowerCase()
        filtered = filtered.filter(task => 
          task.id.toLowerCase().includes(keyword) || 
          task.name.toLowerCase().includes(keyword)
        )
      }
      
      // 任务类型过滤
      if (this.filters.type) {
        filtered = filtered.filter(task => task.type === this.filters.type)
      }
      
      // 任务状态过滤
      if (this.filters.status) {
        filtered = filtered.filter(task => task.status === this.filters.status)
      }
      
      // 日期范围过滤
      if (this.filters.dateRange && this.filters.dateRange.length === 2) {
        filtered = filtered.filter(task => {
          const taskDate = new Date(task.create_time).toISOString().split('T')[0]
          return taskDate >= this.filters.dateRange![0] && taskDate <= this.filters.dateRange![1]
        })
      }
      
      return filtered
    },

    // 获取当前页面的任务（用于虚拟滚动）
    paginatedTasks(): Task[] {
      const filtered = this.filteredTasks
      // 计算起始和结束索引
      const startIndex = (this.currentPage - 1) * this.pageSize
      const endIndex = startIndex + this.pageSize
      // 返回当前页面的数据
      return filtered.slice(startIndex, endIndex)
    },

    // 是否有进度列
    rowHasProgress(): boolean {
      return this.filteredTasks.some(task => task.progress !== undefined)
    },

    // 当前选中任务是否有图表
    taskHasChart(): boolean {
      return this.selectedTask?.result?.has_chart || false
    },

    // 获取任务统计信息
    taskStatistics(): {
      total: number
      running: number
      completed: number
      failed: number
    } {
      return {
        total: this.tasks.length,
        running: this.tasks.filter(task => task.status === 'running').length,
        completed: this.tasks.filter(task => task.status === 'completed').length,
        failed: this.tasks.filter(task => task.status === 'failed').length
      }
    }
  },

  actions: {
    // 获取任务列表
    async fetchTasks() {
      this.loading = true
      this.error = null
      
      try {
        // 使用WebSocket请求任务列表更新
        wsService.requestTaskList()
        
        // 模拟API请求延迟
        await new Promise(resolve => setTimeout(resolve, 500))
      } catch (error) {
        this.error = error instanceof Error ? error.message : '获取任务列表失败'
        console.error('获取任务列表失败:', error)
        
        // 使用模拟数据作为后备
        this.tasks = this.getMockTasks()
        // 重置分页状态
        this.currentPage = 1
        this.hasMoreTasks = this.tasks.length > 0
      } finally {
        this.loading = false
      }
    },

    // 加载更多任务（用于虚拟滚动和懒加载）
    async fetchMoreTasks() {
      // 如果已经没有更多任务或者已经在加载中，则不继续加载
      if (!this.hasMoreTasks || this.loadingMore) {
        return
      }
      
      this.loadingMore = true
      this.error = null
      
      try {
        // 增加当前页码
        this.currentPage += 1
        
        // 使用WebSocket请求更多任务
        wsService.requestMoreTasks(this.currentPage, this.pageSize)
        
        // 模拟API请求延迟
        await new Promise(resolve => setTimeout(resolve, 500))
        
        // 检查是否还有更多任务
        // 实际项目中，应该根据服务器返回的数据判断
        // 这里使用模拟逻辑：如果当前获取的数据量小于pageSize，则认为没有更多任务了
        // 这里只是示例，实际实现需要与后端API配合
        
        // 后备方案：如果WebSocket不可用，使用模拟数据
        if (!wsService.connected.value && this.currentPage <= 3) {
          // 生成一些模拟的更多任务数据
          const moreTasks = this.getMockTasks().map(task => ({
            ...task,
            id: `${task.id}_page${this.currentPage}`
          }))
          this.tasks = [...this.tasks, ...moreTasks]
        }
        
        // 模拟判断是否还有更多任务
        if (this.tasks.length > 200) { // 假设最多有200个任务
          this.hasMoreTasks = false
        }
      } catch (error) {
        this.error = error instanceof Error ? error.message : '加载更多任务失败'
        console.error('加载更多任务失败:', error)
        // 加载失败时，回滚页码
        this.currentPage -= 1
      } finally {
        this.loadingMore = false
      }
    },

    // 设置选中任务
    setSelectedTask(task: Task | null) {
      this.selectedTask = task
      
      if (task) {
        // 订阅该任务的实时更新
        wsService.subscribeTask(task.id)
      }
    },

    // 清除选中任务
    clearSelectedTask() {
      if (this.selectedTask) {
        wsService.unsubscribeTask(this.selectedTask.id)
      }
      this.selectedTask = null
    },

    // 取消任务
  async cancelTask(taskId: string) {
    try {
      // 通过WebSocket发送取消任务请求
      wsService.send({ type: 'cancel_task', task_id: taskId })
      
      // 本地立即更新任务状态，避免用户等待
      const task = this.tasks.find(t => t.id === taskId)
      if (task) {
        task.status = 'cancelled'
        task.logs = (task.logs || '') + '\n任务已被用户取消'
        task.update_time = new Date().toLocaleString('zh-CN')
      }
      
      // 如果当前正在查看的任务被取消，也更新选中任务
      if (this.selectedTask && this.selectedTask.id === taskId) {
        this.selectedTask.status = 'cancelled'
        this.selectedTask.logs = (this.selectedTask.logs || '') + '\n任务已被用户取消'
        this.selectedTask.update_time = new Date().toLocaleString('zh-CN')
      }
    } catch (error) {
      this.error = error instanceof Error ? error.message : '取消任务失败'
      console.error(`取消任务 ${taskId} 失败:`, error)
      throw error
    }
  },
  
  // 批量取消任务
  async batchCancelTasks(taskIds: string[]) {
    try {
      // 通过WebSocket发送批量取消任务请求
      wsService.batchCancelTasks(taskIds)
      
      // 本地立即更新所有任务状态
      taskIds.forEach(taskId => {
        const task = this.tasks.find(t => t.id === taskId)
        if (task) {
          task.status = 'cancelled'
          task.logs = (task.logs || '') + '\n任务已被用户取消'
          task.update_time = new Date().toLocaleString('zh-CN')
        }
        
        // 如果当前正在查看的任务被取消，也更新选中任务
        if (this.selectedTask && this.selectedTask.id === taskId) {
          this.selectedTask.status = 'cancelled'
          this.selectedTask.logs = (this.selectedTask.logs || '') + '\n任务已被用户取消'
          this.selectedTask.update_time = new Date().toLocaleString('zh-CN')
        }
      })
      
      // 操作完成后清除选中状态
      this.clearSelectedTasks()
    } catch (error) {
      this.error = error instanceof Error ? error.message : '批量取消任务失败'
      console.error('批量取消任务失败:', error)
      throw error
    }
  },

    // 删除任务
  async deleteTask(taskId: string) {
    try {
      // 实际项目中应该调用API删除任务
      this.tasks = this.tasks.filter(task => task.id !== taskId)
      
      // 如果删除的是当前查看的任务，清空选中任务
      if (this.selectedTask && this.selectedTask.id === taskId) {
        this.selectedTask = null
      }
      
      // 取消WebSocket订阅
      wsService.unsubscribeTask(taskId)
    } catch (error) {
      this.error = error instanceof Error ? error.message : '删除任务失败'
      console.error(`删除任务 ${taskId} 失败:`, error)
      throw error
    }
  },
  
  // 批量删除任务
  async batchDeleteTasks(taskIds: string[]) {
    try {
      // 实际项目中应该调用API批量删除任务
      this.tasks = this.tasks.filter(task => !taskIds.includes(task.id))
      
      // 如果删除的任务中包含当前查看的任务，清空选中任务
      if (this.selectedTask && taskIds.includes(this.selectedTask.id)) {
        this.selectedTask = null
      }
      
      // 取消所有删除任务的WebSocket订阅
      taskIds.forEach(taskId => {
        wsService.unsubscribeTask(taskId)
      })
      
      // 操作完成后清除选中状态
      this.clearSelectedTasks()
    } catch (error) {
      this.error = error instanceof Error ? error.message : '批量删除任务失败'
      console.error('批量删除任务失败:', error)
      throw error
    }
  },

    // 处理任务状态更新
    handleTaskUpdate(update: TaskStatusUpdate) {
      const taskIndex = this.tasks.findIndex(task => task.id === update.task_id)
      if (taskIndex !== -1) {
        const task = this.tasks[taskIndex]
        
        // 更新任务状态
        if (update.status !== undefined) {
          task.status = update.status
        }
        if (update.progress !== undefined) {
          task.progress = update.progress
        }
        
        // 更新时间
        task.update_time = new Date().toLocaleString('zh-CN')
        
        // 更新日志
        if (update.logs && update.logs.length > 0) {
          if (!task.logs) {
            task.logs = ''
          }
          // 追加新日志，避免重复
          const newLogs = update.logs.join('\n')
          if (!task.logs.includes(newLogs)) {
            task.logs += '\n' + newLogs
          }
        }
        
        // 更新结果
        if (update.result) {
          // 初始化结果对象
          if (!task.result) {
            task.result = {}
          }
          
          // 合并结果数据
          Object.assign(task.result, update.result)
          
          // 如果任务完成，更新完成时间和持续时间
          if (update.status === 'completed') {
            task.complete_time = new Date().toLocaleString('zh-CN')
            // 计算持续时间（秒）
            if (task.create_time) {
              task.duration = Math.floor((new Date().getTime() - new Date(task.create_time).getTime()) / 1000)
            }
          }
        }
        
        // 更新错误信息
        if (update.error && !task.logs?.includes(update.error)) {
          if (!task.logs) {
            task.logs = ''
          }
          task.logs += '\n错误: ' + update.error
        }
        
        // 如果当前查看的任务更新了，更新详情
        if (this.selectedTask && this.selectedTask.id === update.task_id) {
          this.selectedTask = { ...task }
        }
      }
    },

    // 模拟任务进度更新（仅当WebSocket未连接时使用）
    updateRunningTasks() {
      // 只有当WebSocket未连接时才使用模拟更新
      if (!wsService.connected.value) {
        this.tasks.forEach(task => {
          if (task.status === 'running') {
            // 模拟进度更新
            if (task.progress !== undefined && task.progress < 100) {
              task.progress += Math.floor(Math.random() * 5)
              if (task.progress >= 100) {
                task.progress = 100
                task.status = 'completed'
                task.complete_time = new Date().toLocaleString('zh-CN')
                if (task.create_time) {
                  task.duration = Math.floor((new Date().getTime() - new Date(task.create_time).getTime()) / 1000)
                }
                task.logs = (task.logs || '') + '\n任务执行完成'
              }
              task.update_time = new Date().toLocaleString('zh-CN')
            }
          }
        })
        
        // 如果当前查看的任务正在运行，也更新其详情
        if (this.selectedTask && this.selectedTask.status === 'running') {
          const updatedTask = this.tasks.find(t => t.id === this.selectedTask!.id)
          if (updatedTask) {
            this.selectedTask = { ...updatedTask }
          }
        }
      }
    },

    // 设置过滤条件
    setFilters(filters: Partial<TaskState['filters']>) {
      this.filters = { ...this.filters, ...filters }
      // 重置分页状态，以便重新开始加载
      this.resetPagination()
    },

    // 重置分页状态
    resetPagination() {
      this.currentPage = 1
      this.hasMoreTasks = true
    },

    // 格式化任务类型
    formatTaskType(type: string): string {
      const typeMap: Record<string, string> = {
        'backtest': '回测',
        'data_download': '数据下载',
        'data_process': '数据处理'
      }
      return typeMap[type] || type
    },

    // 格式化任务状态
  formatTaskStatus(status: string): string {
    const statusMap: Record<string, string> = {
      'pending': '等待中',
      'running': '运行中',
      'completed': '已完成',
      'failed': '失败',
      'cancelled': '已取消'
    }
    return statusMap[status] || status
  },

    // 获取状态标签类型
  getStatusTagType(status: string): string {
    const typeMap: Record<string, string> = {
      'pending': 'info',
      'running': 'primary',
      'completed': 'success',
      'failed': 'danger',
      'cancelled': 'warning'
    }
    return typeMap[status] || 'default'
  },

    // 格式化时长
    formatDuration(seconds: number): string {
      if (seconds < 60) {
        return seconds + '秒'
      } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60)
        const remainingSeconds = seconds % 60
        return `${minutes}分${remainingSeconds}秒`
      } else {
        const hours = Math.floor(seconds / 3600)
        const minutes = Math.floor((seconds % 3600) / 60)
        return `${hours}时${minutes}分`
      }
    },

    // 清除错误
  clearError() {
    this.error = null
  },
  
  // 选择任务
  selectTask(taskId: string) {
    if (!this.selectedTaskIds.includes(taskId)) {
      this.selectedTaskIds.push(taskId)
    }
  },
  
  // 取消选择任务
  unselectTask(taskId: string) {
    this.selectedTaskIds = this.selectedTaskIds.filter(id => id !== taskId)
  },
  
  // 切换任务选中状态
  toggleTaskSelection(taskId: string) {
    if (this.selectedTaskIds.includes(taskId)) {
      this.unselectTask(taskId)
    } else {
      this.selectTask(taskId)
    }
  },
  
  // 全选/取消全选当前过滤后的任务
  toggleSelectAll() {
    if (this.selectedTaskIds.length === this.filteredTasks.length) {
      // 如果已经全选，则取消全选
      this.clearSelectedTasks()
    } else {
      // 否则全选当前过滤后的任务
      this.selectedTaskIds = this.filteredTasks.map(task => task.id)
    }
  },
  
  // 清除所有选中的任务
  clearSelectedTasks() {
    this.selectedTaskIds = []
  },
  
  // 是否全选
  isAllSelected(): boolean {
    return this.filteredTasks.length > 0 && this.selectedTaskIds.length === this.filteredTasks.length
  },
  
  // 是否部分选中
  isPartiallySelected(): boolean {
    return this.selectedTaskIds.length > 0 && this.selectedTaskIds.length < this.filteredTasks.length
  },

    // 获取模拟任务数据（作为API不可用时的后备）
    getMockTasks(): Task[] {
      return [
        {
          id: 'task_20240712_001',
          name: '策略A回测',
          type: 'backtest',
          status: 'completed',
          progress: 100,
          create_time: '2024-07-12 14:30:00',
          update_time: '2024-07-12 14:45:30',
          complete_time: '2024-07-12 14:45:30',
          duration: 930,
          parameters: {
            strategy_code: 'def strategy(...): ...',
            stock_code: '000001.SZ',
            start_date: '2023-01-01',
            end_date: '2023-12-31',
            initial_capital: 100000
          },
          logs: '回测开始\n加载数据完成\n策略执行中...\n交易信号生成完成\n回测计算完成\n性能指标计算完成\n回测成功',
          result: {
            metrics: {
              total_return: 0.258,
              annual_return: 0.28,
              max_drawdown: -0.125,
              sharpe_ratio: 1.89
            },
            has_chart: true
          }
        },
        {
          id: 'task_20240712_002',
          name: '下载沪深300成分股数据',
          type: 'data_download',
          status: 'completed',
          progress: 100,
          create_time: '2024-07-12 13:45:00',
          update_time: '2024-07-12 14:10:25',
          complete_time: '2024-07-12 14:10:25',
          duration: 1525,
          parameters: {
            stock_codes: ['000001.SZ', '000002.SZ', '600000.SH'],
            data_type: 'daily',
            start_date: '2023-01-01',
            end_date: '2023-12-31',
            format: 'csv'
          },
          logs: '开始下载数据\n连接数据源成功\n下载000001.SZ数据...\n下载000002.SZ数据...\n下载600000.SH数据...\n数据处理完成\n文件生成成功',
          result: {
            file_path: '/data/stock_data_20240712.csv',
            file_size: '1.2MB',
            records_count: 1500
          }
        },
        {
          id: 'task_20240712_003',
          name: '策略B回测',
          type: 'backtest',
          status: 'running',
          progress: 65,
          create_time: '2024-07-12 10:20:00',
          update_time: '2024-07-12 10:35:00',
          parameters: {
            strategy_code: 'def strategy_b(...): ...',
            stock_code: '600000.SH',
            start_date: '2022-01-01',
            end_date: '2023-12-31',
            initial_capital: 200000
          },
          logs: '回测开始\n加载数据完成\n策略执行中...\n正在计算第120天数据...'
        },
        {
          id: 'task_20240711_001',
          name: '下载上证指数数据',
          type: 'data_download',
          status: 'failed',
          create_time: '2024-07-11 16:15:00',
          update_time: '2024-07-11 16:20:30',
          parameters: {
            stock_codes: ['000001.SH'],
            data_type: 'minute',
            start_date: '2024-06-01',
            end_date: '2024-07-01',
            format: 'csv'
          },
          logs: '开始下载数据\n连接数据源成功\n下载000001.SH数据...\n错误：数据源连接超时\n任务失败'
        },
        {
          id: 'task_20240710_001',
          name: '数据清洗处理',
          type: 'data_process',
          status: 'completed',
          progress: 100,
          create_time: '2024-07-10 15:30:00',
          update_time: '2024-07-10 15:45:00',
          complete_time: '2024-07-10 15:45:00',
          duration: 900,
          parameters: {
            input_file: '/data/raw_data.csv',
            output_file: '/data/processed_data.csv',
            operations: ['fill_missing', 'remove_outliers']
          },
          logs: '开始数据处理\n加载原始数据\n填充缺失值\n移除异常值\n数据处理完成\n保存处理后的数据'
        }
      ]
    }
  }
})