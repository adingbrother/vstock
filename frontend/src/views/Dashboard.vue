<template>
  <div class="dashboard-container">
    <h2 class="page-title">数据仪表盘</h2>
    
    <!-- 统计卡片区域 -->
    <div class="stats-cards">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon success">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-info">
            <p class="stat-label">运行中策略</p>
            <p class="stat-value">{{ runningStrategies }}</p>
            <p class="stat-change positive">+2 今日</p>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon primary">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <p class="stat-label">策略总数</p>
            <p class="stat-value">{{ totalStrategies }}</p>
            <p class="stat-change positive">+8 本周</p>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon warning">
            <el-icon><LineChart /></el-icon>
          </div>
          <div class="stat-info">
            <p class="stat-label">平均收益率</p>
            <p class="stat-value">{{ avgReturnRate }}%</p>
            <p class="stat-change positive">+1.2% 较上周</p>
          </div>
        </div>
      </el-card>
      
      <el-card class="stat-card" shadow="hover">
        <div class="stat-content">
          <div class="stat-icon danger">
            <el-icon><Timer /></el-icon>
          </div>
          <div class="stat-info">
            <p class="stat-label">任务队列</p>
            <p class="stat-value">{{ taskQueue }}</p>
            <p class="stat-change negative">-3 较昨日</p>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 图表和数据区域 -->
    <div class="charts-section">
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>策略收益分布</span>
            <el-select v-model="chartTimeRange" class="time-select" @change="handleTimeRangeChange">
              <el-option label="今日" value="today"></el-option>
              <el-option label="本周" value="week"></el-option>
              <el-option label="本月" value="month"></el-option>
              <el-option label="全年" value="year"></el-option>
            </el-select>
          </div>
        </template>
        <div class="chart-container" ref="returnChartRef"></div>
      </el-card>
      
      <el-card class="chart-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>策略运行状态</span>
            <el-select v-model="statusView" class="time-select">
              <el-option label="实时" value="realtime"></el-option>
              <el-option label="历史" value="history"></el-option>
            </el-select>
          </div>
        </template>
        <div class="chart-container" ref="statusChartRef"></div>
      </el-card>
    </div>

    <!-- 策略列表和告警区域 -->
    <div class="bottom-section">
      <!-- 热门策略列表 -->
      <el-card class="list-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>热门策略</span>
            <el-button type="primary" size="small" @click="viewAllStrategies">
              查看全部
            </el-button>
          </div>
        </template>
        <el-table :data="popularStrategies" stripe style="width: 100%">
          <el-table-column prop="name" label="策略名称" min-width="180">
            <template #default="scope">
              <div class="strategy-name">
                <el-tag :type="getStrategyTypeTag(scope.row.type)">{{ scope.row.type }}</el-tag>
                <span>{{ scope.row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="return_rate" label="收益率" width="100">
            <template #default="scope">
              <span :class="scope.row.return_rate > 0 ? 'text-success' : 'text-danger'">
                {{ scope.row.return_rate > 0 ? '+' : '' }}{{ scope.row.return_rate }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="risk_level" label="风险等级" width="100">
            <template #default="scope">
              <el-rate
                v-model="getRiskLevelValue(scope.row.risk_level)"
                disabled
                show-score
                text-color="#67c23a"
                score-template="{value}"
              ></el-rate>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getStrategyStatusTag(scope.row.status)">
                {{ scope.row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="updated_at" label="更新时间" width="150"></el-table-column>
        </el-table>
      </el-card>
      
      <!-- 系统告警 -->
      <el-card class="alert-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>系统告警</span>
            <el-select v-model="alertLevel" class="time-select">
              <el-option label="全部" value="all"></el-option>
              <el-option label="紧急" value="critical"></el-option>
              <el-option label="警告" value="warning"></el-option>
              <el-option label="信息" value="info"></el-option>
            </el-select>
          </div>
        </template>
        <div class="alert-list">
          <div v-for="alert in filteredAlerts" :key="alert.id" class="alert-item" :class="`alert-${alert.level}`">
            <div class="alert-icon">
              <el-icon v-if="alert.level === 'critical'" class="danger"><CircleCloseFilled /></el-icon>
              <el-icon v-else-if="alert.level === 'warning'" class="warning"><WarningFilled /></el-icon>
              <el-icon v-else class="info"><InfoFilled /></el-icon>
            </div>
            <div class="alert-content">
              <p class="alert-title">{{ alert.title }}</p>
              <p class="alert-description">{{ alert.description }}</p>
              <p class="alert-time">{{ alert.time }}</p>
            </div>
            <div class="alert-actions">
              <el-button size="small" @click="handleAlert(alert.id)">处理</el-button>
              <el-button size="small" type="text" @click="dismissAlert(alert.id)">忽略</el-button>
            </div>
          </div>
          <div v-if="filteredAlerts.length === 0" class="no-alerts">
            <el-empty description="暂无告警信息" />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 快速操作区域 -->
    <div class="quick-actions">
      <el-button type="primary" @click="createNewStrategy" icon="Plus">
        新建策略
      </el-button>
      <el-button type="success" @click="runBacktest" icon="RefreshRight">
        运行回测
      </el-button>
      <el-button type="info" @click="importData" icon="Upload">
        导入数据
      </el-button>
      <el-button type="warning" @click="exportReport" icon="Download">
        导出报告
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import {
  TrendCharts,
  Document,
  LineChart,
  Timer,
  CircleCloseFilled,
  WarningFilled,
  InfoFilled,
  Plus,
  RefreshRight,
  Upload,
  Download
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

// 统计数据
const runningStrategies = ref(12)
const totalStrategies = ref(48)
const avgReturnRate = ref(12.8)
const taskQueue = ref(5)

// 图表配置
const chartTimeRange = ref('week')
const statusView = ref('realtime')
const alertLevel = ref('all')
const returnChartRef = ref<HTMLElement>()
const statusChartRef = ref<HTMLElement>()
let returnChart: echarts.ECharts | null = null
let statusChart: echarts.ECharts | null = null

// 监听时间范围变化，更新图表
const handleTimeRangeChange = () => {
  if (returnChart) {
    const data = getDataByTimeRange()
    returnChart.setOption({
      xAxis: {
        data: data.xAxis,
        axisLabel: {
          rotate: chartTimeRange.value === 'year' ? 45 : 0
        }
      },
      series: [{
        data: data.data
      }]
    })
  }
}

// 热门策略数据
const popularStrategies = ref([
  {
    id: 1,
    name: '动量追踪策略',
    type: '技术分析',
    return_rate: 18.5,
    risk_level: 'medium',
    status: '运行中',
    updated_at: '2024-07-12 09:30'
  },
  {
    id: 2,
    name: '均值回归策略',
    type: '统计套利',
    return_rate: -3.2,
    risk_level: 'low',
    status: '已停止',
    updated_at: '2024-07-12 08:15'
  },
  {
    id: 3,
    name: '多因子选股策略',
    type: '基本面',
    return_rate: 15.3,
    risk_level: 'high',
    status: '运行中',
    updated_at: '2024-07-12 07:45'
  },
  {
    id: 4,
    name: '日内高频交易',
    type: '量化',
    return_rate: 8.7,
    risk_level: 'high',
    status: '运行中',
    updated_at: '2024-07-12 06:30'
  },
  {
    id: 5,
    name: '指数增强策略',
    type: '指数',
    return_rate: 12.1,
    risk_level: 'medium',
    status: '已停止',
    updated_at: '2024-07-11 18:00'
  }
])

// 告警数据
const alerts = ref([
  {
    id: 1,
    title: '策略运行异常',
    description: '动量追踪策略在过去10分钟内出现多次信号延迟',
    level: 'warning',
    time: '10分钟前'
  },
  {
    id: 2,
    title: '数据库连接超时',
    description: '与主数据服务器的连接在09:15:30出现短暂中断',
    level: 'critical',
    time: '30分钟前'
  },
  {
    id: 3,
    title: '系统资源不足',
    description: '服务器CPU使用率超过85%，可能影响性能',
    level: 'warning',
    time: '1小时前'
  },
  {
    id: 4,
    title: '回测完成通知',
    description: '多因子选股策略回测任务已成功完成，结果已生成',
    level: 'info',
    time: '2小时前'
  }
])

// 定时器
let updateTimer: number | null = null
const router = useRouter()

// 过滤后的告警列表
const filteredAlerts = computed(() => {
  if (alertLevel.value === 'all') {
    return alerts.value
  }
  return alerts.value.filter(alert => alert.level === alertLevel.value)
})

// 获取策略类型标签颜色
const getStrategyTypeTag = (type: string) => {
  const tagMap: Record<string, string> = {
    '技术分析': 'primary',
    '统计套利': 'success',
    '基本面': 'warning',
    '量化': 'info',
    '指数': 'danger'
  }
  return tagMap[type] || 'default'
}

// 获取风险等级值
const getRiskLevelValue = (risk: string) => {
  const riskMap: Record<string, number> = {
    'low': 2,
    'medium': 3,
    'high': 5
  }
  return riskMap[risk] || 3
}

// 获取策略状态标签颜色
const getStrategyStatusTag = (status: string) => {
  return status === '运行中' ? 'success' : 'info'
}

// 根据时间范围获取数据
const getDataByTimeRange = () => {
  switch (chartTimeRange.value) {
    case 'today':
      return {
        xAxis: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
        data: [2.3, 4.5, 7.8, 12.3, 10.5, 12.8]
      }
    case 'week':
      return {
        xAxis: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
        data: [8.2, 10.5, 7.8, 12.3, 14.5, 9.8, 12.8]
      }
    case 'month':
      return {
        xAxis: ['第1周', '第2周', '第3周', '第4周'],
        data: [12.3, 15.8, 10.5, 18.2]
      }
    case 'year':
      return {
        xAxis: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
        data: [5.2, 8.5, 12.3, 15.8, 10.5, 18.2, 15.8, 20.3, 18.5, 22.1, 19.8, 25.6]
      }
    default:
      return {
        xAxis: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
        data: [8.2, 10.5, 7.8, 12.3, 14.5, 9.8, 12.8]
      }
  }
}

// 初始化收益分布图表
const initReturnChart = () => {
  if (!returnChartRef.value) return
  
  returnChart = echarts.init(returnChartRef.value)
  const data = getDataByTimeRange()
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: data.xAxis,
      axisLabel: {
        rotate: chartTimeRange.value === 'year' ? 45 : 0
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '收益率',
        type: 'line',
        smooth: true,
        data: data.data,
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
        },
        itemStyle: {
          color: '#409EFF'
        },
        lineStyle: {
          color: '#409EFF',
          width: 3
        }
      }
    ]
  }
  
  returnChart.setOption(option)
}

// 初始化状态图表
const initStatusChart = () => {
  if (!statusChartRef.value) return
  
  statusChart = echarts.init(statusChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '策略状态',
        type: 'pie',
        radius: '70%',
        data: [
          { value: runningStrategies.value, name: '运行中' },
          { value: 25, name: '已停止' },
          { value: 8, name: '回测中' },
          { value: 3, name: '异常' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        itemStyle: {
          borderRadius: 5,
          borderColor: '#fff',
          borderWidth: 2
        }
      }
    ]
  }
  
  statusChart.setOption(option)
}

// 更新图表
const updateCharts = () => {
  if (returnChart) {
    // 模拟实时数据更新
    const newData = returnChart.getOption().series?.[0].data as number[] || []
    const updatedData = newData.slice(1).concat([newData[newData.length - 1] + (Math.random() * 2 - 0.5)])
    returnChart.setOption({
      series: [{
        data: updatedData.map(v => Number(v.toFixed(2)))
      }]
    })
  }
}

// 自动更新数据
const startAutoUpdate = () => {
  updateTimer = window.setInterval(() => {
    updateCharts()
    // 模拟数据变化
    avgReturnRate.value = Number((avgReturnRate.value + (Math.random() * 0.2 - 0.1)).toFixed(2))
  }, 5000)
}

// 处理告警
const handleAlert = (alertId: number) => {
  ElMessage.success(`已处理告警 ID: ${alertId}`)
  dismissAlert(alertId)
}

// 忽略告警
const dismissAlert = (alertId: number) => {
  alerts.value = alerts.value.filter(alert => alert.id !== alertId)
}

// 查看全部策略
const viewAllStrategies = () => {
  ElMessage.info('跳转到策略列表页面')
  try {
    router.push('/strategies')
  } catch (error) {
    ElMessage.warning('路由暂不可用')
  }
}

// 新建策略
const createNewStrategy = () => {
  ElMessage.info('打开新建策略对话框')
  try {
    router.push('/backtest')
  } catch (error) {
    ElMessage.warning('路由暂不可用')
  }
}

// 运行回测
const runBacktest = () => {
  ElMessage.info('开始运行回测')
  try {
    router.push('/backtest')
  } catch (error) {
    ElMessage.warning('路由暂不可用')
  }
}

// 导入数据
const importData = () => {
  ElMessage.info('打开数据导入对话框')
  try {
    router.push('/data')
  } catch (error) {
    ElMessage.warning('路由暂不可用')
  }
}

// 导出报告
const exportReport = () => {
  ElMessage.info('开始导出报告')
  // 模拟报告下载
  setTimeout(() => {
    ElMessage.success('报告已生成，请点击下载')
  }, 1500)
}

// 窗口大小变化时重新调整图表
const handleResize = () => {
  returnChart?.resize()
  statusChart?.resize()
}

onMounted(async () => {
  await nextTick()
  initReturnChart()
  initStatusChart()
  startAutoUpdate()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (updateTimer) {
    clearInterval(updateTimer)
  }
  window.removeEventListener('resize', handleResize)
  returnChart?.dispose()
  statusChart?.dispose()
})
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
  color: #303133;
}

/* 统计卡片样式 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.success {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.stat-icon.primary {
  background: linear-gradient(135deg, #409eff, #66b1ff);
}

.stat-icon.warning {
  background: linear-gradient(135deg, #e6a23c, #ebb563);
}

.stat-icon.danger {
  background: linear-gradient(135deg, #f56c6c, #f78989);
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin: 0 0 5px 0;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 5px 0;
}

.stat-change {
  font-size: 12px;
  margin: 0;
}

.stat-change.positive {
  color: #67c23a;
}

.stat-change.negative {
  color: #f56c6c;
}

/* 图表区域样式 */
.charts-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.chart-card {
  height: 350px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 500;
}

.time-select {
  width: 120px;
}

.chart-container {
  width: 100%;
  height: calc(100% - 60px);
}

/* 底部区域样式 */
.bottom-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.list-card {
  min-height: 400px;
}

.alert-card {
  min-height: 400px;
}

.strategy-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.alert-list {
  max-height: 340px;
  overflow-y: auto;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 10px;
  background: #f5f7fa;
  transition: all 0.3s ease;
}

.alert-item:hover {
  background: #ecf5ff;
}

.alert-item.alert-critical {
  border-left: 4px solid #f56c6c;
}

.alert-item.alert-warning {
  border-left: 4px solid #e6a23c;
}

.alert-item.alert-info {
  border-left: 4px solid #409eff;
}

.alert-icon {
  margin-right: 12px;
  font-size: 20px;
}

.alert-icon .danger {
  color: #f56c6c;
}

.alert-icon .warning {
  color: #e6a23c;
}

.alert-icon .info {
  color: #409eff;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 5px 0;
}

.alert-description {
  font-size: 12px;
  color: #606266;
  margin: 0 0 5px 0;
  line-height: 1.4;
}

.alert-time {
  font-size: 11px;
  color: #909399;
  margin: 0;
}

.alert-actions {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.no-alerts {
  padding: 40px 0;
}

/* 快速操作区域 */
.quick-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
}

.quick-actions .el-button {
  min-width: 120px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .bottom-section {
    grid-template-columns: 1fr;
  }
  
  .charts-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 10px;
  }
  
  .stats-cards {
    grid-template-columns: 1fr 1fr;
  }
  
  .stat-content {
    flex-direction: column;
    text-align: center;
    gap: 10px;
  }
  
  .chart-card {
    height: 300px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .quick-actions {
    flex-direction: column;
  }
  
  .quick-actions .el-button {
    width: 100%;
  }
  
  .alert-item {
    flex-direction: column;
  }
  
  .alert-icon {
    margin-bottom: 10px;
  }
  
  .alert-actions {
    flex-direction: row;
    justify-content: flex-end;
    margin-top: 10px;
  }
}

/* 表格样式优化 */
.el-table .el-table__row:hover > td {
  background-color: #f5f7fa;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}
</style>
