// 任务状态枚举
export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

// 任务类型枚举
export enum TaskType {
  BACKTEST = 'backtest',
  DATA_DOWNLOAD = 'data_download',
  DATA_PROCESS = 'data_process',
  MODEL_TRAIN = 'model_train',
  ALERT = 'alert',
  OTHER = 'other'
}

export interface TaskMetrics {
  total_return?: number;     // 总收益率
  annual_return?: number;    // 年化收益率
  max_drawdown?: number;     // 最大回撤
  sharpe_ratio?: number;     // 夏普比率
  trades_count?: number;     // 交易次数
  [key: string]: any;        // 其他可能的指标
}

// 任务结果接口
export interface TaskResult {
  metrics?: TaskMetrics;      // 性能指标
  has_chart?: boolean;        // 是否有图表数据
  file_path?: string;         // 生成文件路径
  file_size?: string;         // 文件大小
  records_count?: number;     // 记录数量
  error?: string;             // 错误信息
  logs?: string;              // 日志信息
  [key: string]: any;         // 其他可能的结果
}

// 任务参数接口
export interface TaskParameters {
  // 通用参数
  [key: string]: any
  
  // 回测任务参数
  strategy_code?: string;     // 策略代码
  stock_code?: string;        // 股票代码
  start_date?: string;        // 开始日期
  end_date?: string;          // 结束日期
  initial_capital?: number;   // 初始资金
  
  // 数据下载任务参数
  stock_codes?: string[];     // 股票代码数组
  data_type?: string;         // 数据类型
  format?: string;            // 格式
  
  // 数据处理任务参数
  input_file?: string;        // 输入文件
  output_file?: string;       // 输出文件
  operations?: string[];      // 操作列表
}

// 任务接口
export interface Task {
  id: string                 // 任务ID改为字符串类型
  name: string               // 任务名称
  type: string               // 任务类型
  status: string             // 任务状态
  progress?: number          // 进度（0-100）
  create_time: string        // 创建时间
  update_time?: string       // 更新时间
  complete_time?: string     // 完成时间
  duration?: number          // 持续时间（秒）
  parameters: TaskParameters // 任务参数
  logs?: string              // 任务日志
  result?: TaskResult        // 任务结果
  error?: string             // 错误信息
}

// 任务筛选条件接口
export type TaskFilter = {
  searchKeyword?: string;     // 搜索关键词
  taskType?: string;          // 任务类型筛选
  taskStatus?: string;        // 任务状态筛选
  dateRange?: [string, string]; // 日期范围筛选
};

// 任务状态更新接口（用于WebSocket消息）
export interface TaskStatusUpdate {
  task_id: string            // 任务ID改为字符串类型
  status?: string            // 状态更新
  progress?: number          // 进度更新
  logs?: string[]            // 日志更新（多条）
  result?: TaskResult        // 结果更新
  error?: string             // 错误信息
}