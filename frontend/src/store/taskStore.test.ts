import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTaskStore } from './taskStore'
import { wsService } from '../services/websocketService'

// Mock websocketService
vi.mock('../services/websocketService', () => ({
  wsService: {
    requestTaskList: vi.fn(),
    subscribeTask: vi.fn(),
    unsubscribeTask: vi.fn(),
    send: vi.fn(),
    batchCancelTasks: vi.fn()
  }
}))

describe('TaskStore', () => {
  let taskStore: any

  const mockTasks = [
    {
      id: 'task-1',
      name: 'Backtest Task',
      type: 'backtest',
      status: 'completed',
      create_time: '2024-01-01 10:00:00',
      update_time: '2024-01-01 10:30:00',
      duration: 1800
    },
    {
      id: 'task-2',
      name: 'Data Download',
      type: 'data_download',
      status: 'running',
      progress: 50,
      create_time: '2024-01-01 11:00:00',
      update_time: '2024-01-01 11:15:00'
    },
    {
      id: 'task-3',
      name: 'Data Process',
      type: 'data_process',
      status: 'failed',
      create_time: '2024-01-01 12:00:00',
      update_time: '2024-01-01 12:05:00'
    }
  ]

  beforeEach(() => {
    setActivePinia(createPinia())
    taskStore = useTaskStore()
    taskStore.tasks = [...mockTasks]
  })

  it('应该正确初始化状态', () => {
    expect(taskStore.tasks).toHaveLength(3)
    expect(taskStore.selectedTaskIds).toEqual([])
    expect(taskStore.loading).toBe(false)
    expect(taskStore.error).toBe(null)
  })

  it('应该正确过滤任务', () => {
    // 测试关键词过滤
    taskStore.setFilters({ keyword: 'Backtest' })
    expect(taskStore.filteredTasks).toHaveLength(1)
    expect(taskStore.filteredTasks[0].id).toBe('task-1')

    // 重置过滤器
    taskStore.setFilters({ keyword: '', type: '', status: '' })
  })

  it('应该正确获取任务统计信息', () => {
    const stats = taskStore.taskStatistics
    expect(stats.total).toBe(3)
    expect(stats.running).toBe(1)
    expect(stats.completed).toBe(1)
    expect(stats.failed).toBe(1)
  })

  it('应该正确设置选中任务', () => {
    const task = mockTasks[0]
    taskStore.setSelectedTask(task)
    expect(taskStore.selectedTask).toStrictEqual(task)
    expect(wsService.subscribeTask).toHaveBeenCalledWith(task.id)
  })

  it('应该正确清除选中任务', () => {
    const task = mockTasks[0]
    taskStore.setSelectedTask(task)
    taskStore.clearSelectedTask()
    expect(taskStore.selectedTask).toBe(null)
    expect(wsService.unsubscribeTask).toHaveBeenCalledWith(task.id)
  })

  it('应该正确处理任务选择操作', () => {
    // 选择任务
    taskStore.selectTask('task-1')
    expect(taskStore.selectedTaskIds).toContain('task-1')

    // 取消选择
    taskStore.unselectTask('task-1')
    expect(taskStore.selectedTaskIds).not.toContain('task-1')

    // 切换选择
    taskStore.toggleTaskSelection('task-1')
    expect(taskStore.selectedTaskIds).toContain('task-1')
    taskStore.toggleTaskSelection('task-1')
    expect(taskStore.selectedTaskIds).not.toContain('task-1')
  })

  it('应该正确格式化任务类型和状态', () => {
    expect(taskStore.formatTaskType('backtest')).toBe('回测')
    expect(taskStore.formatTaskType('data_download')).toBe('数据下载')
    expect(taskStore.formatTaskType('data_process')).toBe('数据处理')
    
    expect(taskStore.formatTaskStatus('pending')).toBe('等待中')
    expect(taskStore.formatTaskStatus('running')).toBe('运行中')
    expect(taskStore.formatTaskStatus('completed')).toBe('已完成')
    expect(taskStore.formatTaskStatus('failed')).toBe('失败')
    expect(taskStore.formatTaskStatus('cancelled')).toBe('已取消')
  })

  it('应该正确格式化任务持续时间', () => {
    expect(taskStore.formatDuration(1800)).toBe('30分0秒')
    expect(taskStore.formatDuration(3600)).toBe('1时0分')
    expect(taskStore.formatDuration(60)).toBe('1分0秒')
    expect(taskStore.formatDuration(10)).toBe('10秒')
  })
})
