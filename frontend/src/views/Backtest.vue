<template>
  <div class="backtest-container">
    <h2 class="page-title">策略回测</h2>
    
    <el-card class="backtest-form">
      <template #header>
        <div class="card-header">
          <span>回测参数设置</span>
        </div>
      </template>
      <el-form ref="backtestFormRef" :model="backtestForm" :rules="rules" label-width="120px">
        <el-form-item label="策略名称" prop="strategy_name">
          <el-input v-model="backtestForm.strategy_name" placeholder="请输入策略名称"></el-input>
        </el-form-item>
        <el-form-item label="策略代码" prop="strategy_code">
          <el-input
            v-model="backtestForm.strategy_code"
            type="textarea"
            :rows="6"
            placeholder="请输入Python策略代码"
          ></el-input>
        </el-form-item>
        <el-form-item label="股票代码" prop="stock_code">
          <el-input v-model="backtestForm.stock_code" placeholder="例如: 000001.SZ"></el-input>
        </el-form-item>
        <el-form-item label="回测时间范围">
          <div class="date-range">
            <el-date-picker
              v-model="backtestForm.start_date"
              type="date"
              placeholder="开始日期"
              style="width: 45%"
            ></el-date-picker>
            <span style="margin: 0 10px; color: #909399">至</span>
            <el-date-picker
              v-model="backtestForm.end_date"
              type="date"
              placeholder="结束日期"
              style="width: 45%"
            ></el-date-picker>
          </div>
        </el-form-item>
        <el-form-item label="初始资金">
          <el-input-number
            v-model="backtestForm.initial_capital"
            :min="10000"
            :max="10000000"
            :step="10000"
            placeholder="初始资金"
          ></el-input-number>
        </el-form-item>
        <el-form-item label="交易费率">
          <el-input-number
            v-model="backtestForm.fee_rate"
            :min="0"
            :max="0.1"
            :step="0.0001"
            :precision="4"
            placeholder="交易费率"
          ></el-input-number>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="submitBacktest" :loading="submitting">
            <el-icon v-if="!submitting"><Play /></el-icon>
            <el-icon v-else><Loading /></el-icon>
            开始回测
          </el-button>
          <el-button @click="resetForm">重置表单</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <div v-if="taskId" class="backtest-result">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>回测结果 (任务ID: {{ taskId }})</span>
            <el-button
              size="small"
              type="text"
              @click="checkStatus"
              :loading="checkingStatus"
            >
              <el-icon><Refresh /></el-icon> 刷新状态
            </el-button>
          </div>
        </template>
        <div v-if="!taskStatus" class="loading-state">
          <el-skeleton :rows="5" animated />
        </div>
        <div v-else-if="taskStatus.status === 'running'">
          <el-progress :percentage="taskStatus.progress || 0" status="primary" />
          <p class="status-text">回测进行中... {{ taskStatus.message || '正在处理数据' }}</p>
        </div>
        <div v-else-if="taskStatus.status === 'completed'">
          <el-tabs type="border-card">
            <el-tab-pane label="性能指标">
              <div class="metrics-grid">
                <el-card class="metric-card">
                  <div class="metric-title">总收益率</div>
                  <div class="metric-value">{{ formatPercent(taskResult.total_return || 0) }}</div>
                </el-card>
                <el-card class="metric-card">
                  <div class="metric-title">年化收益率</div>
                  <div class="metric-value">{{ formatPercent(taskResult.annual_return || 0) }}</div>
                </el-card>
                <el-card class="metric-card">
                  <div class="metric-title">最大回撤</div>
                  <div class="metric-value">{{ formatPercent(taskResult.max_drawdown || 0) }}</div>
                </el-card>
                <el-card class="metric-card">
                  <div class="metric-title">夏普比率</div>
                  <div class="metric-value">{{ (taskResult.sharpe_ratio || 0).toFixed(2) }}</div>
                </el-card>
              </div>
              <div class="chart-container" ref="chartContainerRef">
                <div v-if="!chartInstance.value" class="chart-placeholder">
                  {{ taskStatus.value?.status === 'completed' ? '加载图表中...' : '回测完成后显示图表' }}
                </div>
              </div>
            </el-tab-pane>
            <el-tab-pane label="交易记录">
              <el-table :data="taskResult.trades || []" stripe style="width: 100%">
                <el-table-column prop="date" label="交易日期" />
                <el-table-column prop="action" label="操作" />
                <el-table-column prop="price" label="价格" />
                <el-table-column prop="quantity" label="数量" />
                <el-table-column prop="amount" label="金额" />
              </el-table>
            </el-tab-pane>
            <el-tab-pane label="日志">
              <el-scrollbar wrap-class="log-container">
                <pre class="log-content">{{ taskResult.logs || '暂无日志' }}</pre>
              </el-scrollbar>
            </el-tab-pane>
          </el-tabs>
        </div>
        <div v-else-if="taskStatus.status === 'failed'">
          <el-alert
            title="回测失败"
            type="error"
            :description="taskStatus.message || '未知错误'"
            show-icon
          ></el-alert>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElForm, ElMessageBox } from 'element-plus'
import { Play, Loading, Refresh } from '@element-plus/icons-vue'
import axios from 'axios'
import * as echarts from 'echarts'

const backtestFormRef = ref<InstanceType<typeof ElForm> | null>(null)
const chartContainerRef = ref<HTMLElement | null>(null)

// 回测表单数据
const backtestForm = reactive({
  strategy_name: '',
  strategy_code: `def strategy(data, params):\n    # 简单的均线策略示例\n    import pandas as pd\n    import numpy as np\n    \n    # 计算5日均线和20日均线\n    data['ma5'] = data['close'].rolling(window=5).mean()\n    data['ma20'] = data['close'].rolling(window=20).mean()\n    \n    # 生成交易信号\n    data['signal'] = 0\n    data.loc[data['ma5'] > data['ma20'], 'signal'] = 1  # 买入信号\n    data.loc[data['ma5'] < data['ma20'], 'signal'] = 0  # 卖出信号\n    \n    return data['signal']`,
  stock_code: '000001.SZ',
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  initial_capital: 100000,
  fee_rate: 0.0003
})

// 表单验证规则
const rules = reactive({
  strategy_name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' },
    { min: 2, max: 50, message: '策略名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  strategy_code: [
    { required: true, message: '请输入策略代码', trigger: 'blur' },
    { min: 10, message: '策略代码不能少于10个字符', trigger: 'blur' }
  ],
  stock_code: [
    { required: true, message: '请输入股票代码', trigger: 'blur' },
    { pattern: /^[0-9]{6}\.[A-Z]{2}$/, message: '股票代码格式错误，例如: 000001.SZ', trigger: 'blur' }
  ]
})

// 任务状态
const taskId = ref('')
const taskStatus = ref(null)
const taskResult = ref({})
const submitting = ref(false)
const checkingStatus = ref(false)
const chartInstance = ref<echarts.ECharts | null>(null)
let statusCheckTimer: number | null = null

// 格式化百分比
const formatPercent = (value: number) => {
  return (value * 100).toFixed(2) + '%'
}

// 初始化收益图表
const initReturnChart = () => {
  if (!chartContainerRef.value || !taskResult.value) return
  
  // 销毁旧图表
  if (chartInstance.value) {
    chartInstance.value.dispose()
  }
  
  chartInstance.value = echarts.init(chartContainerRef.value)
  
  // 模拟收益曲线数据
  const dates = ['01-01', '02-01', '03-01', '04-01', '05-01', '06-01', '07-01', '08-01', '09-01', '10-01', '11-01', '12-01']
  const strategyReturns = [0, 0.032, 0.058, 0.085, 0.072, 0.115, 0.148, 0.123, 0.165, 0.198, 0.225, 0.258]
  const benchmarkReturns = [0, 0.015, 0.028, 0.035, 0.042, 0.055, 0.068, 0.072, 0.085, 0.092, 0.105, 0.123]
  
  const option = {
    title: {
      text: '策略收益曲线对比',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: function(params: any) {
        let result = params[0].axisValue + '<br/>'
        params.forEach((item: any) => {
          const percent = (item.value * 100).toFixed(2) + '%'
          result += item.marker + item.seriesName + ': ' + percent + '<br/>'
        })
        return result
      }
    },
    legend: {
      data: ['策略收益', '基准收益'],
      bottom: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: function(value: number) {
          return (value * 100).toFixed(0) + '%'
        }
      }
    },
    series: [
      {
        name: '策略收益',
        type: 'line',
        smooth: true,
        data: strategyReturns,
        lineStyle: {
          width: 3,
          color: '#409EFF'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {
              offset: 0,
              color: 'rgba(64, 158, 255, 0.6)'
            },
            {
              offset: 1,
              color: 'rgba(64, 158, 255, 0.1)'
            }
          ])
        }
      },
      {
        name: '基准收益',
        type: 'line',
        smooth: true,
        data: benchmarkReturns,
        lineStyle: {
          width: 2,
          color: '#67c23a',
          type: 'dashed'
        }
      }
    ]
  }
  
  chartInstance.value.setOption(option)
}

// 开始自动检查任务状态
const startStatusCheck = () => {
  // 清除之前的定时器
  stopStatusCheck()
  
  // 每3秒检查一次状态
  statusCheckTimer = window.setInterval(() => {
    if (taskStatus.value?.status === 'running') {
      checkStatus()
    } else {
      stopStatusCheck()
    }
  }, 3000)
}

// 停止自动检查任务状态
const stopStatusCheck = () => {
  if (statusCheckTimer) {
    clearInterval(statusCheckTimer)
    statusCheckTimer = null
  }
}

// 窗口大小变化处理
const handleResize = () => {
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
}

// 提交回测
const submitBacktest = async () => {
  if (!backtestFormRef.value) return
  
  await backtestFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        // 模拟API调用
        // const response = await axios.post('/api/v1/backtest/submit', backtestForm)
        
        // 生成模拟任务ID
        taskId.value = `backtest_${Date.now()}`
        
        // 模拟任务状态
        taskStatus.value = {
          status: 'running',
          progress: 0,
          message: '正在初始化回测环境'
        }
        
        ElMessage.success('回测任务已提交')
        
        // 开始轮询状态
        checkStatus()
        startStatusCheck()
      } catch (error) {
        ElMessage.error('提交失败: ' + (error as Error).message)
        console.error('提交回测失败:', error)
      } finally {
        submitting.value = false
      }
    }
  })
}

// 检查状态
const checkStatus = async () => {
  if (!taskId.value) return
  
  checkingStatus.value = true
  try {
    // 模拟API调用
    // const response = await axios.get(`/api/v1/backtest/status/${taskId.value}`)
    
    // 模拟任务进度更新
    if (taskStatus.value?.status === 'running') {
      const currentProgress = taskStatus.value.progress || 0
      let newProgress = currentProgress + Math.floor(Math.random() * 15)
      
      if (newProgress >= 100) {
        newProgress = 100
        taskStatus.value.status = 'completed'
        taskStatus.value.message = '回测完成'
        
        // 设置回测结果
        taskResult.value = {
          total_return: 0.258,
          annual_return: 0.28,
          max_drawdown: -0.125,
          sharpe_ratio: 1.89,
          trades: [
            { date: '2023-02-01', action: '买入', price: 13.5, quantity: 1000, amount: 13500 },
            { date: '2023-04-15', action: '卖出', price: 15.2, quantity: 1000, amount: 15200 },
            { date: '2023-06-10', action: '买入', price: 14.8, quantity: 1000, amount: 14800 },
            { date: '2023-11-20', action: '卖出', price: 16.8, quantity: 1000, amount: 16800 }
          ],
          logs: '回测开始\n加载数据完成\n策略执行中...\n交易信号生成完成\n回测计算完成\n性能指标计算完成\n回测成功'
        }
        
        ElMessage.success('回测完成！')
        
        // 等待DOM更新后初始化图表
        nextTick(() => {
          initReturnChart()
        })
      } else {
        // 更新进度消息
        let progressMessage = '正在执行'
        if (newProgress < 20) progressMessage = '正在初始化回测环境'
        else if (newProgress < 40) progressMessage = '正在加载历史数据'
        else if (newProgress < 60) progressMessage = '正在执行策略逻辑'
        else if (newProgress < 80) progressMessage = '正在计算交易信号'
        else if (newProgress < 95) progressMessage = '正在计算性能指标'
        
        taskStatus.value.progress = newProgress
        taskStatus.value.message = progressMessage
      }
    }
  } catch (error) {
    console.error('检查任务状态失败:', error)
    ElMessage.error('检查状态失败，请稍后重试')
  } finally {
    checkingStatus.value = false
  }
}

// 重置表单
const resetForm = async () => {
  if (taskStatus.value?.status === 'running') {
    await ElMessageBox.confirm('有正在运行的回测任务，确定要重置吗？', '确认重置', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
  }
  
  backtestFormRef.value?.resetFields()
  taskId.value = ''
  taskStatus.value = null
  taskResult.value = {}
  
  // 清理图表和定时器
  stopStatusCheck()
  if (chartInstance.value) {
    chartInstance.value.dispose()
    chartInstance.value = null
  }
}

// 组件挂载和卸载
onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  stopStatusCheck()
  if (chartInstance.value) {
    chartInstance.value.dispose()
    chartInstance.value = null
  }
})
</script>

<style scoped>
.backtest-container {
  padding: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
  color: #303133;
}

.backtest-form {
  margin-bottom: 30px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 500;
}

.date-range {
  display: flex;
  align-items: center;
}

.backtest-result {
  margin-top: 30px;
}

.loading-state {
  padding: 20px 0;
}

.status-text {
  text-align: center;
  margin-top: 10px;
  color: #409eff;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}

.metric-card {
  text-align: center;
}

.metric-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 10px;
}

.metric-value {
  font-size: 28px;
  font-weight: 600;
  color: #409eff;
}

.chart-container {
  height: 400px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.chart-placeholder {
  color: #909399;
  font-size: 14px;
}

.log-container {
  height: 400px;
}

.log-content {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .date-range {
    flex-direction: column;
    align-items: stretch;
  }
  
  .date-range .el-date-picker {
    width: 100% !important;
    margin-bottom: 10px;
  }
  
  .date-range span {
    display: none;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
