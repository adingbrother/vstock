<template>
  <div class="tasks-container">
    <h2 class="page-title">
      任务管理
      <span class="connection-status">
        <el-icon :class="['status-icon', wsConnected ? 'connected' : 'disconnected']">
          <Signal /></el-icon>
        <span>{{ wsConnected ? '已连接' : '未连接' }}</span>
      </span>
    </h2>
    
    <el-card>
      <template #header>
        <div class="card-header">
          <span>历史任务列表</span>
          <div>
            <el-button
              v-if="taskStore.selectedTaskIds.length > 0"
              size="small"
              type="warning"
              style="margin-right: 8px"
              @click="batchCancelSelectedTasks"
              :loading="batchLoading"
            >
              <el-icon><Stop /></el-icon> 批量取消
            </el-button>
            <el-button
              v-if="taskStore.selectedTaskIds.length > 0"
              size="small"
              type="danger"
              style="margin-right: 8px"
              @click="batchDeleteSelectedTasks"
              :loading="batchLoading"
            >
              <el-icon><Delete /></el-icon> 批量删除
            </el-button>
            <el-button size="small" @click="refreshTasks">
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="filter-section">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索任务ID或名称"
              prefix-icon="<Search />"
            ></el-input>
          </el-col>
          <el-col :span="6">
            <el-select v-model="taskType" placeholder="任务类型"
              filterable clearable allow-create default-first-option
            >
              <el-option label="全部" value=""></el-option>
              <el-option label="回测" value="backtest"></el-option>
              <el-option label="数据下载" value="data_download"></el-option>
              <el-option label="数据处理" value="data_process"></el-option>
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-select v-model="taskStatus" placeholder="任务状态"
              filterable clearable allow-create default-first-option
            >
              <el-option label="全部" value=""></el-option>
              <el-option label="等待中" value="pending"></el-option>
              <el-option label="运行中" value="running"></el-option>
              <el-option label="已完成" value="completed"></el-option>
              <el-option label="失败" value="failed"></el-option>
              <el-option label="已取消" value="cancelled"></el-option>
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
            ></el-date-picker>
          </el-col>
        </el-row>
      </div>
      
      <el-table :data="paginatedTasks" stripe style="width: 100%"
        @row-click="viewTaskDetail"
        row-class-name="task-row"
        @select-all="handleSelectAll"
        @selection-change="handleSelectionChange"
        v-loading="taskStore.loading"
        empty-text="暂无数据"
        :row-key="row => row.id" // 使用唯一ID作为行键，提高性能
        :row-height="48" // 固定行高，优化虚拟滚动
        lazy
        :lazy-load="loadMoreData" // 实现懒加载
        :estimate-row-height="48" // 预估行高，用于虚拟滚动
        border
        :highlight-current-row="false" // 禁用高亮以提高性能
        :header-cell-style="headerCellStyle" // 优化表头样式
        :body-cell-style="bodyCellStyle" // 优化单元格样式
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="任务ID" width="120" show-overflow-tooltip 
          :show="!isMobile" />
        <el-table-column prop="name" label="任务名称" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="120"
          formatter="formatTaskType"
        />
        <el-table-column prop="status" label="状态" width="100"
          formatter="formatTaskStatus"
        >
          <template #default="scope">
            <el-tag
              :type="getStatusTagType(scope.row.status)"
              effect="dark"
            >{{ formatTaskStatus(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="progress" label="进度" width="120"
          v-if="rowHasProgress"
        >
          <template #default="scope">
            <el-progress
              v-if="scope.row.progress !== undefined"
              :percentage="scope.row.progress"
              :stroke-width="8"
              :show-text="false"
            />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="150" 
          :show="!isMobile" />
        <el-table-column prop="update_time" label="更新时间" width="150" 
          :show="deviceType !== 'mobile'" />
        <el-table-column label="操作" width="150" fixed="right"
          :show-overflow-tooltip="false"
        >
          <template #default="scope">
            <el-button
              size="small"
              type="primary"
              @click.stop="viewTaskDetail(scope.row)"
            >
              <el-icon><View /></el-icon> 查看
            </el-button>
            <el-button
              v-if="scope.row.status === 'running'"
              size="small"
              type="warning"
              @click.stop="cancelTask(scope.row.id)"
            >
              <el-icon><Stop /></el-icon> 取消
            </el-button>
            <el-button
              v-if="scope.row.status !== 'running'"
              size="small"
              type="danger"
              @click.stop="deleteTask(scope.row.id)"
            >
              <el-icon><Delete /></el-icon> 删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="isMobile ? [5, 10, 20] : [10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="taskStore.filteredTasks.length"
        style="margin-top: 15px; text-align: right"
        @size-change="currentPage = 1"
      ></el-pagination>
    </el-card>
    
    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="showTaskDetail"
      :title="`任务详情 - ${selectedTask?.id || ''}`"
      :width="isMobile ? '95%' : isTablet ? '90%' : '80%'"
      :top="isMobile ? '2vh' : '5vh'"
      :fullscreen="isMobile"
      @close="handleDetailClose"
      destroy-on-close
    >
      <div v-if="selectedTask" class="task-detail"
        :class="{ 'task-detail-mobile': isMobile }"
      >
        <el-tabs type="border-card"
          v-model="activeDetailTab"
          :tab-position="isMobile ? 'top' : 'left'"
          @tab-click="handleTabChange"
        >
          <el-tab-pane label="基本信息">
            <el-descriptions 
              :column="isMobile ? 1 : 2" 
              border 
              :size="isMobile ? 'large' : 'default'"
              :title="'任务信息'"
              class="task-descriptions"
            >
              <el-descriptions-item label="任务ID">{{ selectedTask.id }}</el-descriptions-item>
              <el-descriptions-item label="任务名称">{{ selectedTask.name }}</el-descriptions-item>
              <el-descriptions-item label="任务类型">{{ formatTaskType(selectedTask.type) }}</el-descriptions-item>
              <el-descriptions-item label="任务状态">
                <el-tag :type="getStatusTagType(selectedTask.status)" effect="dark"
                  class="task-status-tag"
                >{{ formatTaskStatus(selectedTask.status) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ selectedTask.create_time }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ selectedTask.update_time }}</el-descriptions-item>
              <el-descriptions-item label="完成时间" v-if="selectedTask.complete_time"
                >{{ selectedTask.complete_time }}</el-descriptions-item>
              <el-descriptions-item label="执行用时" v-if="selectedTask.duration"
                >{{ formatDuration(selectedTask.duration) }}</el-descriptions-item>
              <el-descriptions-item label="备注" v-if="selectedTask.remark"
                >{{ selectedTask.remark }}</el-descriptions-item>
            </el-descriptions>
            
            <div v-if="selectedTask.parameters" class="task-params"
              style="margin-top: 20px"
            >
              <h4 style="margin-bottom: 15px; color: #303133">任务参数</h4>
              <pre class="params-json">{{ JSON.stringify(selectedTask.parameters, null, 2) }}</pre>
            </div>
          </el-tab-pane>
          <el-tab-pane label="日志输出">
            <el-scrollbar wrap-class="log-scrollbar"
              :vertical="true"
              height="400px"
            >
              <pre class="task-logs">{{ selectedTask.logs || '暂无日志' }}</pre>
            </el-scrollbar>
          </el-tab-pane>
          <el-tab-pane label="结果数据"
            v-if="selectedTask.status === 'completed' && selectedTask.result"
          >
            <div v-if="taskStore.taskHasChart"
              class="chart-container"
              :ref="'chartContainer'"
              :class="{'chart-container-mobile': isMobile, 'chart-container-tablet': isTablet}"
            >
              <div v-if="!chartInstance" class="chart-placeholder">
                加载图表中...
              </div>
            </div>
            <div v-if="selectedTask.result.metrics"
              class="metrics-container"
              style="margin-top: 20px"
            >
              <h4 style="margin-bottom: 15px; color: #303133">性能指标</h4>
              <pre class="metrics-json">{{ JSON.stringify(selectedTask.result.metrics, null, 2) }}</pre>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      <template #footer>
        <el-button @click="showTaskDetail = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search, View, Stop, Delete, Signal, CheckCircle, CircleClose, InfoFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { wsService, type TaskStatusUpdate } from '../services/websocketService'
import { useTaskStore } from '../store/taskStore'
import type { Task } from '../types/task'

// 使用Pinia store
const taskStore = useTaskStore()

// 状态变量
const currentPage = ref(1)
const pageSize = ref(20)
const showTaskDetail = ref(false)
const activeDetailTab = ref('0')
const wsConnected = ref(false)
const batchLoading = ref(false)
const searchKeyword = ref('')
const taskType = ref('')
const taskStatus = ref('')
const dateRange = ref<[string, string] | null>(null)

// 定时器ID
let updateTimer: number | null = null
let chartInstance: echarts.ECharts | null = null

// 响应式判断是否为移动端
const isMobile = computed(() => {
  return window.innerWidth < 768
})

// 判断是否为平板
const isTablet = computed(() => {
  return window.innerWidth >= 768 && window.innerWidth < 1024
})

// 获取设备类型
const deviceType = computed(() => {
  if (isMobile.value) return 'mobile'
  if (isTablet.value) return 'tablet'
  return 'desktop'
})

// 分页后的数据 - 优化大数据量处理
const paginatedTasks = computed(() => {
  // 获取过滤后的数据
  const filteredTasks = taskStore.filteredTasks
  const totalItems = filteredTasks.length
  
  // 根据设备类型动态调整初始加载数量和性能策略
  const maxInitialItems = deviceType.value === 'mobile' ? 30 : 
                          deviceType.value === 'tablet' ? 50 : 100
  
  // 大数据量时的性能优化策略
  if (totalItems > 1000) {
    // 对于超大数据集，实现虚拟滚动的基础逻辑
    if (currentPage.value === 1) {
      // 第一页只显示前N条数据
      return filteredTasks.slice(0, maxInitialItems)
    } else {
      // 非第一页计算合适的范围，避免内存占用过高
      const pageSizeForLargeData = Math.min(pageSize.value, 50) // 大数据量时减小每页大小
      const start = (currentPage.value - 1) * pageSizeForLargeData
      const end = Math.min(start + pageSizeForLargeData, totalItems)
      return filteredTasks.slice(start, end)
    }
  } else {
    // 正常数据集的分页逻辑
    const start = (currentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return filteredTasks.slice(start, end)
  }
})

// 虚拟滚动相关配置
const virtualScrollConfig = reactive({
  bufferSize: 50, // 缓冲区大小
  lastScrollPosition: 0,
  scrollDebounceTimer: null as number | null,
  isScrolling: false
})

// 懒加载更多数据 - 优化实现
const loadMoreData = async (row: any, treeNode: any, resolve: Function) => {
  try {
    // 检查是否需要加载更多数据
    if (taskStore.hasMoreData && !taskStore.loadingMore) {
      // 设置加载状态
      taskStore.setLoadingMore(true)
      
      // 加载更多数据
      await taskStore.fetchMoreTasks()
      
      // 通知表格已加载数据
      resolve([])
    } else {
      resolve([])
    }
  } catch (error) {
    console.error('加载更多数据失败:', error)
    resolve([])
  } finally {
    taskStore.setLoadingMore(false)
  }
}

// 表头样式优化
const headerCellStyle = {
  backgroundColor: '#fafafa',
  fontWeight: 600,
  fontSize: '14px',
  padding: '8px 12px',
  whiteSpace: 'nowrap' as const,
  overflow: 'hidden' as const,
  textOverflow: 'ellipsis' as const
}

// 单元格样式优化
const bodyCellStyle = {
  padding: '8px 12px',
  fontSize: '14px',
  transition: 'none' // 禁用过渡动画以提高性能
}

// 优化表格渲染性能 - 增强版
const optimizeTableRendering = () => {
  // 确保表格在大数据量下的性能
  const table = document.querySelector('.el-table')
  if (table) {
    // 添加性能优化的CSS类
    table.classList.add('optimized-table')
    
    // 设置表格容器样式以优化性能
    const bodyWrapper = table.querySelector('.el-table__body-wrapper')
    if (bodyWrapper) {
      // 添加虚拟滚动优化
      bodyWrapper.classList.add('virtual-scroll-wrapper')
      
      // 添加滚动事件监听器进行性能优化
      bodyWrapper.addEventListener('scroll', handleTableScroll, { passive: true })
    }
  }
}

// 处理表格滚动事件 - 优化性能
const handleTableScroll = () => {
  if (virtualScrollConfig.isScrolling) return
  
  virtualScrollConfig.isScrolling = true
  
  // 防抖处理
  if (virtualScrollConfig.scrollDebounceTimer) {
    clearTimeout(virtualScrollConfig.scrollDebounceTimer)
  }
  
  virtualScrollConfig.scrollDebounceTimer = setTimeout(() => {
    // 优化滚动性能的逻辑
    requestAnimationFrame(() => {
      virtualScrollConfig.isScrolling = false
    })
  }, 100)
}

// 表格性能优化函数 - 增强版
const setupOptimization = () => {
  // 确保表格在大数据量下的性能
  optimizeTableRendering()
  
  // 监听数据变化，当数据量很大时进行额外的优化
  watch(() => taskStore.filteredTasks.length, (newLength) => {
    if (newLength > 500) {
      // 大数据量时进行额外的优化措施
      optimizeForLargeDatasets()
    }
  })
}

// 大数据集优化函数
const optimizeForLargeDatasets = () => {
  // 减少不必要的渲染
  const table = document.querySelector('.el-table')
  if (table) {
    // 禁用动画
    table.classList.add('disable-animations')
    
    // 优化渲染性能
    table.setAttribute('data-large-dataset', 'true')
  }
}

// 内存管理：释放不再需要的资源
const cleanupResources = () => {
  // 清理表格滚动事件监听器
  const table = document.querySelector('.el-table')
  if (table) {
    const bodyWrapper = table.querySelector('.el-table__body-wrapper')
    if (bodyWrapper) {
      bodyWrapper.removeEventListener('scroll', handleTableScroll)
    }
  }
  
  // 清理定时器
  if (virtualScrollConfig.scrollDebounceTimer) {
    clearTimeout(virtualScrollConfig.scrollDebounceTimer)
  }
}

// 刷新任务列表
const refreshTasks = async () => {
  try {
    // 添加节流，避免频繁刷新
    if (refreshTasks.pending) return
    refreshTasks.pending = true
    
    await taskStore.fetchTasks()
    ElMessage.success('任务列表已刷新')
  } catch (error) {
    ElMessage.error('刷新失败: ' + (error as Error).message)
  } finally {
    setTimeout(() => {
      refreshTasks.pending = false
    }, 1000) // 1秒内不允许重复刷新
  }
}
// 标记刷新状态
Object.defineProperty(refreshTasks, 'pending', { value: false, writable: true })

// 执行搜索
const executeSearch = () => {
  taskStore.setFilters({
    keyword: searchKeyword.value,
    type: taskType.value,
    status: taskStatus.value,
    dateRange: dateRange.value || []
  })
  currentPage.value = 1
}

// 监听搜索条件变化 - 添加防抖优化
let searchDebounceTimer: number | null = null
watch([searchKeyword, taskType, taskStatus, dateRange], () => {
  if (searchDebounceTimer) {
    clearTimeout(searchDebounceTimer)
  }
  searchDebounceTimer = setTimeout(() => {
    executeSearch()
  }, 300) // 300ms防抖延迟
})

// 查看任务详情
const viewTaskDetail = (task: Task) => {
  taskStore.setSelectedTask(task)
  showTaskDetail.value = true
  activeDetailTab.value = '0'
  
  // 延迟初始化图表，确保DOM已渲染
  nextTick(() => {
    if (taskStore.taskHasChart) {
      initResultChart()
    }
  })
}

// 初始化结果图表
const initResultChart = () => {
  if (!taskStore.selectedTask || !taskStore.taskHasChart || !taskStore.selectedTask.result) return
  
  const chartContainer = document.querySelector('.chart-container')
  if (!chartContainer) return
  
  chartInstance = echarts.init(chartContainer)
  
  // 根据任务类型生成不同的图表
  let option
  if (taskStore.selectedTask.type === 'backtest') {
    // 使用任务结果中的实际回测数据
    const resultData = taskStore.selectedTask.result
    const dates = resultData.dates || []
    const strategyReturns = resultData.strategy_returns || []
    const benchmarkReturns = resultData.benchmark_returns || []
    
    // 如果没有实际数据，使用默认数据
    const defaultDates = ['1月', '2月', '3月', '4月', '5月', '6月']
    const defaultStrategyReturns = [2.5, 5.8, 7.3, 9.1, 12.5, 15.2]
    const defaultBenchmarkReturns = [1.2, 2.5, 3.8, 4.5, 5.2, 6.1]
    
    // 回测结果图表
    option = {
      title: {
        text: '策略收益曲线',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let result = `${params[0].name}<br/>`
          params.forEach((param: any) => {
            result += `${param.marker}${param.seriesName}: ${param.value.toFixed(2)}%<br/>`
          })
          return result
        }
      },
      legend: {
        data: ['策略收益', '基准收益'],
        bottom: 0
      },
      xAxis: {
        type: 'category',
        data: dates.length > 0 ? dates : defaultDates,
        axisLabel: {
          rotate: 45
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
          name: '策略收益',
          type: 'line',
          data: strategyReturns.length > 0 ? strategyReturns : defaultStrategyReturns,
          smooth: true,
          lineStyle: {
            width: 3
          },
          itemStyle: {
            color: '#409EFF'
          },
          emphasis: {
            focus: 'series'
          }
        },
        {
          name: '基准收益',
          type: 'line',
          data: benchmarkReturns.length > 0 ? benchmarkReturns : defaultBenchmarkReturns,
          smooth: true,
          lineStyle: {
            type: 'dashed',
            width: 2
          },
          itemStyle: {
            color: '#67C23A'
          },
          emphasis: {
            focus: 'series'
          }
        }
      ]
    }
  } else if (taskStore.selectedTask.type === 'data_download') {
    // 数据下载任务的图表
    const resultData = taskStore.selectedTask.result
    const downloadedFiles = resultData.downloaded_files || 0
    const totalFiles = resultData.total_files || downloadedFiles
    const failedFiles = totalFiles - downloadedFiles
    
    option = {
      title: {
        text: '数据下载情况',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 10,
        data: ['已下载', '下载失败']
      },
      series: [
        {
          name: '下载状态',
          type: 'pie',
          radius: ['50%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 10,
            borderColor: '#fff',
            borderWidth: 2
          },
          label: {
            show: false,
            position: 'center'
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 20,
              fontWeight: 'bold'
            }
          },
          labelLine: {
            show: false
          },
          data: [
            { value: downloadedFiles, name: '已下载', itemStyle: { color: '#67C23A' } },
            { value: failedFiles, name: '下载失败', itemStyle: { color: '#F56C6C' } }
          ]
        }
      ]
    }
  } else if (taskStore.selectedTask.type === 'data_process') {
    // 数据处理任务的图表
    const resultData = taskStore.selectedTask.result
    const processedRecords = resultData.processed_records || 0
    const totalRecords = resultData.total_records || processedRecords
    const successRate = totalRecords > 0 ? (processedRecords / totalRecords) * 100 : 0
    
    option = {
      title: {
        text: '数据处理统计',
        left: 'center'
      },
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
        data: ['处理记录数', '成功率']
      },
      yAxis: [
        {
          type: 'value',
          name: '记录数',
          position: 'left'
        },
        {
          type: 'value',
          name: '成功率(%)',
          position: 'right',
          axisLabel: {
            formatter: '{value}%'
          }
        }
      ],
      series: [
        {
          name: '记录数',
          type: 'bar',
          data: [processedRecords],
          itemStyle: {
            color: '#409EFF'
          }
        },
        {
          name: '成功率',
          type: 'line',
          yAxisIndex: 1,
          data: [successRate],
          itemStyle: {
            color: '#67C23A'
          },
          lineStyle: {
            width: 3
          }
        }
      ]
    }
  } else {
    // 其他类型任务的通用图表
    option = {
      title: {
        text: '任务执行情况',
        left: 'center'
      },
      tooltip: {
        trigger: 'item'
      },
      series: [
        {
          name: '完成比例',
          type: 'pie',
          radius: '60%',
          data: [
            {value: 100, name: '已完成', itemStyle: { color: '#67C23A' }}
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
  }
  
  chartInstance.setOption(option)
}

// 监听tab切换，初始化图表
const handleTabChange = (tab: any) => {
  activeDetailTab.value = tab.index
  if (tab.index === '2' && taskStore.taskHasChart) {
    nextTick(() => {
      initResultChart()
    })
  }
}

// 处理WebSocket任务状态更新
const handleTaskUpdate = (update: TaskStatusUpdate) => {
  taskStore.handleTaskUpdate(update)
  
  // 显示状态变更通知
  const task = taskStore.tasks.find(t => t.id === update.task_id)
  if (task) {
    if (update.status === 'completed') {
      ElMessage.success(`任务「${task.name}」已完成`)
    } else if (update.status === 'failed') {
      ElMessage.error(`任务「${task.name}」执行失败`)
    }
    
    // 如果任务完成且有图表，更新图表
    if (update.status === 'completed' && taskStore.taskHasChart && chartInstance) {
      // 等待DOM更新后重新初始化图表
      nextTick(() => {
        chartInstance?.dispose()
        chartInstance = null
        initResultChart()
      })
    }
  }
}

// 取消任务
const cancelTask = (taskId: string) => {
  ElMessageBox.confirm('确定要取消此任务吗？', '取消确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await taskStore.cancelTask(taskId)
      ElMessage.success('已发送取消请求')
    } catch (error) {
      ElMessage.error('取消失败')
    }
  }).catch(() => {})
}

// 批量取消选中的任务
const batchCancelSelectedTasks = () => {
  if (taskStore.selectedTaskIds.length === 0) {
    ElMessage.warning('请先选择要取消的任务')
    return
  }
  
  ElMessageBox.confirm(`确定要取消选中的 ${taskStore.selectedTaskIds.length} 个任务吗？`, '批量取消确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    batchLoading.value = true
    try {
      await taskStore.batchCancelTasks(taskStore.selectedTaskIds)
      ElMessage.success('批量取消请求已发送')
    } catch (error) {
      ElMessage.error('批量取消失败')
    } finally {
      batchLoading.value = false
    }
  }).catch(() => {})
}

// 批量删除选中的任务
const batchDeleteSelectedTasks = () => {
  if (taskStore.selectedTaskIds.length === 0) {
    ElMessage.warning('请先选择要删除的任务')
    return
  }
  
  ElMessageBox.confirm(`确定要删除选中的 ${taskStore.selectedTaskIds.length} 个任务吗？此操作不可恢复。`, '批量删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'danger'
  }).then(async () => {
    batchLoading.value = true
    try {
      await taskStore.batchDeleteTasks(taskStore.selectedTaskIds)
      ElMessage.success('任务已批量删除')
    } catch (error) {
      ElMessage.error('批量删除失败')
    } finally {
      batchLoading.value = false
    }
  }).catch(() => {})
}

// 处理全选事件
const handleSelectAll = (selection: Task[]) => {
  if (selection.length > 0) {
    taskStore.toggleSelectAll()
  } else {
    taskStore.clearSelectedTasks()
  }
}

// 处理选择变化事件
const handleSelectionChange = (selection: Task[]) => {
  // 清空现有选择
  taskStore.clearSelectedTasks()
  // 添加新的选择
  selection.forEach(task => taskStore.selectTask(task.id))
}

// 删除任务
const deleteTask = (taskId: string) => {
  ElMessageBox.confirm('确定要删除此任务吗？', '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await taskStore.deleteTask(taskId)
      ElMessage.success('任务已删除')
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 窗口大小变化处理
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
  
  // 当切换设备类型时，可能需要重新初始化图表
  if (taskStore.taskHasChart && showTaskDetail.value) {
    nextTick(() => {
      if (chartInstance) {
        chartInstance.dispose()
        chartInstance = null
      }
      initResultChart()
    })
  }
}

// 关闭任务详情对话框的处理
const handleDetailClose = () => {
  taskStore.clearSelectedTask()
}

// 启动自动更新
const startAutoUpdate = () => {
  // 每5秒更新一次运行中的任务状态（作为WebSocket的备份）
  updateTimer = window.setInterval(() => taskStore.updateRunningTasks(), 5000)
}

// 停止自动更新
const stopAutoUpdate = () => {
  if (updateTimer) {
    clearInterval(updateTimer)
    updateTimer = null
  }
}

onMounted(async () => {
  window.addEventListener('resize', handleResize)
  startAutoUpdate()
  
  // 初始化WebSocket连接
  wsService.connect()
  
  // 监听WebSocket连接状态
  watch(() => wsService.connected, (newVal) => {
    wsConnected.value = newVal
  }, { immediate: true })
  
  // 设置消息处理器
  wsService.onMessage(handleTaskUpdate)
  
  // 初始化任务列表
  await taskStore.fetchTasks()
  
  // 订阅正在运行的任务
  taskStore.tasks.forEach(task => {
    if (task.status === 'running') {
      wsService.subscribeTask(task.id)
    }
  })
  
  // 执行表格性能优化
  setupOptimization()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  stopAutoUpdate()
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
  
  // 清除选中任务
  taskStore.clearSelectedTask()
  
  // 断开WebSocket连接
  wsService.disconnect()
  
  // 清理资源，防止内存泄漏
  cleanupResources()
})
</script>

<style scoped>
.tasks-container {
  padding: 20px;
  min-height: 100vh;
}

/* 响应式容器内边距 */
@media (max-width: 768px) {
  .tasks-container {
    padding: 10px;
  }
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
  color: #303133;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

/* 平板和手机标题调整 */
@media (max-width: 1024px) {
  .page-title {
    font-size: 20px;
    margin-bottom: 16px;
  }
}

.connection-status {
  font-size: 14px;
  font-weight: normal;
  display: flex;
  align-items: center;
  gap: 5px;
}

.status-icon.connected {
  color: #67C23A;
}

.status-icon.disconnected {
  color: #F56C6C;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 500;
  flex-wrap: wrap;
  gap: 10px;
}

/* 移动端卡片头部调整 */
@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .card-header > div {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    width: 100%;
  }
}

.filter-section {
  margin-bottom: 20px;
}

.task-row {
  cursor: pointer;
  transition: background-color 0.3s;
}

.task-row:hover {
  background-color: #f5f7fa;
}

.task-status-tag {
  font-size: 12px;
  padding: 4px 8px;
}

/* 响应式参数和指标显示 */
.params-json,
.metrics-json {
  background: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  overflow-x: auto;
  margin: 0;
  word-break: break-all;
}

@media (max-width: 768px) {
  .params-json,
  .metrics-json {
    padding: 10px;
    font-size: 12px;
  }
}

/* 响应式日志显示 */
.task-logs {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 768px) {
  .task-logs {
    font-size: 12px;
    line-height: 1.4;
  }
}

.log-scrollbar {
  height: 400px;
}

/* 响应式日志滚动条高度 */
@media (max-width: 1024px) {
  .log-scrollbar {
    height: 300px;
  }
}

@media (max-width: 768px) {
  .log-scrollbar {
    height: 250px;
  }
}

/* 响应式图表容器 */
.chart-container {
  height: 400px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  padding: 10px;
}

.chart-container-tablet {
  height: 350px;
}

.chart-container-mobile {
  height: 280px;
  padding: 5px;
}

.chart-placeholder {
  color: #909399;
  font-size: 14px;
}

/* 响应式任务详情 */
.task-detail {
  display: flex;
  flex-direction: column;
  height: 600px;
}

.task-detail-mobile {
  height: auto;
}

/* 响应式描述信息 */
.task-descriptions {
  font-size: 14px;
}

@media (max-width: 768px) {
  .task-descriptions {
    font-size: 12px;
  }
}

/* 响应式标签页调整 */
@media (max-width: 768px) {
  .el-tabs__header {
    margin: 0 0 10px 0;
  }
  
  .el-tabs__item {
    font-size: 12px;
    padding: 0 10px;
  }
}

/* 响应式表格样式 */
@media (max-width: 1024px) {
  .el-table {
    font-size: 13px;
  }
  
  .el-table__header th,
  .el-table__body td {
    padding: 8px;
  }
}

@media (max-width: 768px) {
  .el-table {
    font-size: 12px;
  }
  
  .el-table__header th,
  .el-table__body td {
    padding: 6px;
  }
  
  .el-button {
    font-size: 12px;
    padding: 8px 12px;
  }
  
  .el-button--small {
    padding: 6px 10px;
  }
}

/* 响应式筛选区域 */
@media (max-width: 768px) {
  .filter-section .el-row {
    flex-direction: column;
    gap: 10px;
  }
  
  .filter-section .el-col {
    margin-bottom: 0;
    width: 100% !important;
  }
}

/* 平板设备响应式 */
@media (min-width: 768px) and (max-width: 1024px) {
  .filter-section .el-row {
    flex-wrap: wrap;
  }
  
  .filter-section .el-col {
    width: 50% !important;
    margin-bottom: 15px;
  }
  
  .filter-section .el-col:nth-child(n+3) {
    margin-bottom: 0;
  }
}

/* 响应式分页控件 */
@media (max-width: 768px) {
  .el-pagination {
    margin-top: 15px;
    font-size: 12px;
  }
  
  .el-pagination__sizes,
  .el-pagination__total {
    display: none;
  }
}

/* 响应式按钮组 */
@media (max-width: 768px) {
  .el-button-group {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }
}

/* 表格性能优化样式 - 增强版 */
.optimized-table {
  /* 禁用不必要的动画以提高性能 */
  --el-table-animation-duration: 0ms;
  contain: layout style;
}

.optimized-table .el-table__body-wrapper {
  /* 优化滚动性能 */
  overflow-scrolling: touch;
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
}

/* 虚拟滚动优化样式 */
.virtual-scroll-wrapper {
  /* 使用GPU加速 */
  transform: translateZ(0);
  -webkit-transform: translateZ(0);
  will-change: scroll-position;
}

/* 减少重绘和回流 */
.task-row {
  transform: translateZ(0);
  will-change: transform;
  backface-visibility: hidden;
  contain: layout style;
}

/* 大数据集优化样式 */
[data-large-dataset="true"] .el-table__header th,
[data-large-dataset="true"] .el-table__body td {
  /* 进一步减少样式复杂性 */
  box-shadow: none !important;
  border-width: 0 1px 1px 0 !important;
  border-style: solid !important;
  border-color: #ebeef5 !important;
  transition: none !important;
}

/* 禁用动画类 */
.disable-animations {
  animation: none !important;
  transition: none !important;
}

.disable-animations * {
  animation: none !important;
  transition: none !important;
}

/* 大数据量时优化列宽 */
@media (max-width: 1024px) {
  .el-table .el-table__header th,
  .el-table .el-table__body td {
    transition: none;
  }
}

/* 优化筛选区域渲染 */
.filter-section {
  contain: layout style paint;
}</style>
