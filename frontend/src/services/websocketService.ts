import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'

// WebSocket状态类型
export interface TaskStatusUpdate {
  task_id: string
  status: 'running' | 'completed' | 'failed' | 'pending'
  progress: number
  result?: any
  error?: string
  logs?: string[]
}

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000 // 初始重连延迟1秒
  private messageQueue: string[] = [] // 断线时的消息队列
  private isConnecting = false
  private subscribedTasks: Set<string> = new Set() // 记录已订阅的任务ID
  
  // 状态管理
  public connected = ref(false)
  public connectionStatus = ref<'disconnected' | 'connecting' | 'connected'>('disconnected')
  
  // 事件回调
  private onMessageCallback: ((data: TaskStatusUpdate) => void) | null = null
  private onErrorCallback: ((error: Event) => void) | null = null
  private onCloseCallback: ((event: CloseEvent) => void) | null = null
  
  constructor() {
    // 监听页面可见性变化，在页面重新可见时检查连接状态
    document.addEventListener('visibilitychange', this.handleVisibilityChange)
  }
  
  // 初始化WebSocket连接
  public connect(url?: string) {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return
    }
    
    this.isConnecting = true
    this.connectionStatus.value = 'connecting'
    
    // 如果没有提供URL，使用环境变量或默认值
    const wsUrl = url || import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/tasks'
    
    try {
      this.ws = new WebSocket(wsUrl)
      
      this.ws.onopen = this.handleOpen
      this.ws.onmessage = this.handleMessage
      this.ws.onerror = this.handleError
      this.ws.onclose = this.handleClose
    } catch (error) {
      console.error('WebSocket连接错误:', error)
      ElMessage.error('WebSocket连接失败')
      this.isConnecting = false
      this.connectionStatus.value = 'disconnected'
      this.scheduleReconnect()
    }
  }
  
  // 断开连接
  public disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Client initiated disconnection')
      this.ws = null
    }
    this.connected.value = false
    this.connectionStatus.value = 'disconnected'
    this.isConnecting = false
    this.reconnectAttempts = 0
  }
  
  // 发送消息
  public send(message: any) {
    const messageStr = typeof message === 'string' ? message : JSON.stringify(message)
    
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(messageStr)
    } else {
      // 断线时加入消息队列
      this.messageQueue.push(messageStr)
      // 尝试重连
      if (this.connectionStatus.value === 'disconnected') {
        this.connect()
      }
    }
  }
  
  // 批量取消任务
  public batchCancelTasks(taskIds: string[]) {
    this.send({ type: 'batch_cancel', task_ids: taskIds })
  }
  
  // 订阅任务状态更新
  public subscribeTask(taskId: string) {
    this.subscribedTasks.add(taskId)
    this.send({ type: 'subscribe', task_id: taskId })
  }
  
  // 取消订阅任务状态更新
  public unsubscribeTask(taskId: string) {
    this.subscribedTasks.delete(taskId)
    this.send({ type: 'unsubscribe', task_id: taskId })
  }
  
  // 恢复所有任务订阅
  private restoreSubscriptions() {
    this.subscribedTasks.forEach(taskId => {
      this.send({ type: 'subscribe', task_id: taskId })
    })
  }
  
  // 请求任务列表更新
  public requestTaskList() {
    this.send({ type: 'get_tasks' })
  }
  
  // 请求更多任务（用于虚拟滚动和懒加载）
  public requestMoreTasks(page: number, pageSize: number) {
    this.send({ 
      type: 'get_more_tasks', 
      page: page, 
      page_size: pageSize 
    })
  }
  
  // 发送心跳包
  public sendHeartbeat() {
    this.send({ type: 'heartbeat', timestamp: Date.now() })
  }
  
  // 设置事件监听器
  public onMessage(callback: (data: TaskStatusUpdate) => void) {
    this.onMessageCallback = callback
  }
  
  public onError(callback: (error: Event) => void) {
    this.onErrorCallback = callback
  }
  
  public onClose(callback: (event: CloseEvent) => void) {
    this.onCloseCallback = callback
  }
  
  // WebSocket事件处理
  private handleOpen = () => {
    console.log('WebSocket连接已建立')
    ElMessage.success('实时监控已连接')
    
    this.connected.value = true
    this.connectionStatus.value = 'connected'
    this.isConnecting = false
    this.reconnectAttempts = 0
    
    // 发送队列中的消息
    this.flushMessageQueue()
    
    // 恢复任务订阅
    this.restoreSubscriptions()
    
    // 启动心跳机制
    this.startHeartbeat()
  }
  
  private handleMessage = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data) as TaskStatusUpdate
      
      // 忽略心跳响应
      if (data.type === 'heartbeat_response') {
        return
      }
      
      if (this.onMessageCallback) {
        this.onMessageCallback(data)
      }
    } catch (error) {
      console.error('解析WebSocket消息失败:', error)
    }
  }
  
  private handleError = (error: Event) => {
    console.error('WebSocket错误:', error)
    
    if (this.onErrorCallback) {
      this.onErrorCallback(error)
    }
  }
  
  private handleClose = (event: CloseEvent) => {
    console.log(`WebSocket连接已关闭: ${event.code} - ${event.reason}`)
    
    this.connected.value = false
    this.connectionStatus.value = 'disconnected'
    this.isConnecting = false
    
    if (this.onCloseCallback) {
      this.onCloseCallback(event)
    }
    
    // 非正常关闭时尝试重连
    if (event.code !== 1000) {
      this.scheduleReconnect()
    }
  }
  
  // 重连机制
  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket重连次数已达上限')
      ElMessage.error('实时监控连接失败，请刷新页面重试')
      return
    }
    
    this.reconnectAttempts++
    // 指数退避 + 随机抖动 (±10%)
    const baseDelay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    const jitter = baseDelay * 0.1 * (Math.random() * 2 - 1) // -10% 到 +10% 的随机抖动
    const delay = Math.max(1000, Math.min(30000, baseDelay + jitter)) // 限制在1秒到30秒之间
    
    console.log(`将在 ${Math.round(delay)}ms 后进行第 ${this.reconnectAttempts} 次重连`)
    
    setTimeout(() => {
      this.connect()
    }, delay)
  }
  
  // 发送队列中的消息
  private flushMessageQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift()
      if (message) {
        this.ws?.send(message)
      }
    }
  }
  
  // 心跳机制
  private heartbeatTimer: number | null = null
  
  private startHeartbeat() {
    this.stopHeartbeat()
    
    // 每30秒发送一次心跳
    this.heartbeatTimer = window.setInterval(() => {
      this.sendHeartbeat()
    }, 30000)
  }
  
  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }
  
  // 处理页面可见性变化
  private handleVisibilityChange = () => {
    if (!document.hidden) {
      // 页面重新可见时检查连接状态
      if (this.connectionStatus.value === 'disconnected') {
        this.connect()
      } else if (this.connected.value) {
        // 发送心跳确认连接是否正常
        this.sendHeartbeat()
      }
    }
  }
  
  // 销毁资源
  public destroy() {
    this.disconnect()
    this.stopHeartbeat()
    document.removeEventListener('visibilitychange', this.handleVisibilityChange)
    this.onMessageCallback = null
    this.onErrorCallback = null
    this.onCloseCallback = null
  }
}

// 导出单例实例
export const wsService = new WebSocketService()

// 导出Vue组合式函数
export function useWebSocket() {
  const ws = wsService
  
  onMounted(() => {
    // 自动连接
    ws.connect()
  })
  
  onUnmounted(() => {
    // 清理资源
    ws.destroy()
  })
  
  return {
    ws,
    connected: ws.connected,
    connectionStatus: ws.connectionStatus
  }
}
