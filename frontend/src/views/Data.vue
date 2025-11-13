<template>
  <div class="data-container">
    <h2 class="page-title">数据管理</h2>
    
    <el-card>
          <template #header>
            <div class="card-header">
              <span>文件统计概览</span>
            </div>
          </template>
          <div class="stats-container">
            <div class="stat-item">
              <div class="stat-value">{{ fileStats.total }}</div>
              <div class="stat-label">总文件数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ fileStats.csv }}</div>
              <div class="stat-label">CSV文件</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ fileStats.excel }}</div>
              <div class="stat-label">Excel文件</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatFileSize(fileStats.totalSize) }}</div>
              <div class="stat-label">总存储大小</div>
            </div>
          </div>
        </el-card>
        <br>

<el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="数据下载">
        <el-card class="download-form">
          <template #header>
            <div class="card-header">
              <span>下载股票数据</span>
            </div>
          </template>
          <el-form ref="downloadFormRef" :model="downloadForm" label-width="120px">
            <el-form-item label="股票代码" prop="stock_codes">
              <el-input
                v-model="downloadForm.stock_codes"
                type="textarea"
                :rows="3"
                placeholder="请输入股票代码，每行一个（例如：000001.SZ）"
                show-word-limit
                maxlength="500"
              ></el-input>
              <div class="el-form-item__help" style="color: #67c23a; margin-top: 5px;">
                支持批量下载多个股票数据，最多50个
              </div>
            </el-form-item>
            <el-form-item label="数据类型" prop="data_type">
              <el-select v-model="downloadForm.data_type" placeholder="请选择数据类型">
                <el-option label="日线数据" value="daily"></el-option>
                <el-option label="分钟线数据" value="minute"></el-option>
                <el-option label="基本面数据" value="fundamental"></el-option>
              <el-select>
            </el-form-item>
            <el-form-item label="时间范围">
              <div class="date-range">
                <el-date-picker
                  v-model="downloadForm.start_date"
                  type="date"
                  placeholder="开始日期"
                  style="width: 45%"
                ></el-date-picker>
                <span style="margin: 0 10px; color: #909399">至</span>
                <el-date-picker
                  v-model="downloadForm.end_date"
                  type="date"
                  placeholder="结束日期"
                  style="width: 45%"
                ></el-date-picker>
              </div>
            </el-form-item>
            <el-form-item label="数据源" prop="source">
              <el-select v-model="downloadForm.source" placeholder="请选择数据源">
                <el-option label="本地数据库" value="local"></el-option>
                <el-option label="公开API" value="public_api"></el-option>
                <el-option label="自定义数据源" value="custom"></el-option>
              <el-select>
            </el-form-item>
            <el-form-item label="导出格式" prop="format">
              <el-select v-model="downloadForm.format" placeholder="请选择导出格式">
                <el-option label="CSV" value="csv"></el-option>
                <el-option label="Excel" value="excel"></el-option>
                <el-option label="JSON" value="json"></el-option>
              <el-select>
            </el-form-item>
            <el-form-item>
              <el-button 
                type="primary" 
                @click="submitDownload" 
                :loading="submitting"
                size="large"
                style="min-width: 150px;"
              >
                <el-icon v-if="!submitting"><Download /></el-icon>
                <el-icon v-else><Loading /></el-icon>
                开始下载
              </el-button>
              <el-button 
                @click="resetDownloadForm"
                size="large"
                style="margin-left: 15px;"
              >
                <el-icon><Refresh /></el-icon> 重置表单
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="文件管理">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>下载历史文件</span>
              <div>
                <el-button size="small" @click="refreshFiles">
                  <el-icon><Refresh /></el-icon> 刷新
                </el-button>
                <el-button 
                  size="small" 
                  type="danger" 
                  @click="batchDeleteFiles"
                  :disabled="selectedFiles.length === 0"
                  style="margin-left: 10px"
                >
                  <el-icon><Delete /></el-icon> 批量删除
                  <span v-if="selectedFiles.length > 0">({{ selectedFiles.length }})</span>
                </el-button>
              </div>
            </div>
          </template>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索文件名"
            prefix-icon="<Search />"
            style="margin-bottom: 15px"
          ></el-input>
          <el-table 
            :data="filteredFiles" 
            stripe 
            style="width: 100%"
            @select="(selection, row) => toggleSelectFile(row, selection.includes(row))"
            @select-all="(selection) => {
              if (selection.length === filteredFiles.value.length) {
                selectedFiles.value = [...filteredFiles.value]
              } else {
                selectedFiles.value = []
              }
            }"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="name" label="文件名" show-overflow-tooltip />
            <el-table-column prop="size" label="大小" formatter="formatFileSize" />
            <el-table-column prop="type" label="类型" />
            <el-table-column prop="create_time" label="创建时间" />
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="scope">
                <div class="action-buttons">
                  <el-tooltip effect="dark" content="下载文件" placement="top">
                    <el-button 
                      size="small" 
                      type="primary" 
                      plain
                      @click="downloadFile(scope.row)"
                    >
                      <el-icon><Download /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip effect="dark" content="预览文件" placement="top">
                    <el-button 
                      size="small" 
                      type="success" 
                      plain
                      @click="selectedFile = scope.row; activeTab = '2'"
                    >
                      <el-icon><View /></el-icon>
                    </el-button>
                  </el-tooltip>
                  <el-tooltip effect="dark" content="删除文件" placement="top">
                    <el-button 
                      size="small" 
                      type="danger" 
                      plain
                      @click="deleteFile(scope.row.id)"
                    >
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            :total="filteredFiles.length"
            style="margin-top: 15px"
          ></el-pagination>
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="数据预览">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>数据预览器</span>
            </div>
          </template>
          <div v-if="selectedFile">
            <h3 style="margin-bottom: 20px; color: #303133">{{ selectedFile.name }}</h3>
            <el-skeleton :loading="isPreviewLoading" animated :rows="10">
              <template #template>
                <div class="preview-skeleton">
                  <el-table :data="[]" stripe style="width: 100%">
                    <el-table-column label="列1" width="180" />
                    <el-table-column label="列2" width="180" />
                    <el-table-column label="列3" />
                    <el-table-column label="列4" width="120" />
                  </el-table>
                </div>
              </template>
              <el-table :data="previewData" stripe style="width: 100%" v-if="!isPreviewLoading">
                <el-table-column v-for="(col, index) in previewColumns" :key="index" :prop="col" :label="col" />
              </el-table>
            </el-skeleton>
          </div>
          <div v-else class="no-data">
            <el-empty description="请从文件管理中选择一个文件进行预览"></el-empty>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
    
    <!-- 下载任务状态对话框 -->
    <el-dialog v-model="showStatusDialog" title="下载状态" width="600px" class="slide-in-right">
      <div v-if="downloadTaskStatus" class="progress-container">
        <div class="progress-text">
          <span>下载进度</span>
          <span>{{ downloadTaskStatus.progress || 0 }}%</span>
        </div>
        <el-progress 
          :percentage="downloadTaskStatus.progress || 0" 
          :status="downloadTaskStatus.status === 'failed' ? 'exception' : 'success'"
          :color="{
            '0%': '#667eea',
            '100%': '#764ba2'
          }"
          stroke-width="12"
        />
        <p class="status-text">{{ downloadTaskStatus.message || '正在下载...' }}</p>
        <div v-if="downloadTaskStatus.status === 'completed'" style="margin-top: 20px; display: flex; justify-content: center;">
          <el-button type="primary" @click="downloadResultFile" size="large">
            <el-icon><Download /></el-icon> 下载结果文件
          </el-button>
        </div>
      </div>
      <template #footer>
        <el-button @click="showStatusDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElForm } from 'element-plus'
import { Download, Loading, Refresh, Search, Delete, View } from '@element-plus/icons-vue'
import axios from 'axios'
import { wsService, type TaskStatusUpdate } from '../services/websocketService'

const downloadFormRef = ref<InstanceType<typeof ElForm> | null>(null)
const activeTab = ref('0')

// 下载表单数据
const downloadForm = reactive({
  stock_codes: '000001.SZ\n000002.SZ\n600000.SH',
  data_type: 'daily',
  start_date: '2023-01-01',
  end_date: '2023-12-31',
  source: 'local',
  format: 'csv'
})

// 状态变量
const submitting = ref(false)
const showStatusDialog = ref(false)
const downloadTaskId = ref('')
const downloadTaskStatus = ref<{
  status: string
  progress: number
  message: string
} | null>(null)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const selectedFile = ref(null)
const isWsConnected = ref(false)

// 模拟文件数据
const files = ref([
  { id: 1, name: '000001.SZ_daily_2023.csv', size: 1024 * 150, type: 'csv', create_time: '2024-07-10 14:30:00' },
  { id: 2, name: '000002.SZ_daily_2023.csv', size: 1024 * 145, type: 'csv', create_time: '2024-07-10 14:35:00' },
  { id: 3, name: '600000.SH_daily_2023.csv', size: 1024 * 132, type: 'csv', create_time: '2024-07-10 14:40:00' },
  { id: 4, name: 'stock_fundamental_2023.json', size: 1024 * 512, type: 'json', create_time: '2024-07-11 10:20:00' },
  { id: 5, name: 'market_data_summary.xlsx', size: 1024 * 2048, type: 'excel', create_time: '2024-07-12 09:15:00' }
])

// 预览数据
const previewData = ref<any[]>([])
const previewColumns = ref<string[]>([])
const isPreviewLoading = ref(false)

// 文件统计数据
const fileStats = ref({
  total: 0,
  csv: 0,
  excel: 0,
  parquet: 0,
  totalSize: 0
})

// 计算属性：过滤后的文件列表
const filteredFiles = computed(() => {
  const keyword = searchKeyword.value.toLowerCase()
  return files.value.filter(file => 
    file.name.toLowerCase().includes(keyword)
  )
})

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(k)), sizes.length - 1)
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 提交下载任务
const submitDownload = async () => {
  if (!downloadFormRef.value) return
  
  await downloadFormRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        // 分割股票代码
        const stockCodes = downloadForm.stock_codes.split('\n')
          .map(code => code.trim())
          .filter(code => code)
        
        // 准备API请求数据
        const requestData = {
          stock_list: stockCodes,
          start_date: downloadForm.start_date.replace(/-/g, ''),
          end_date: downloadForm.end_date.replace(/-/g, ''),
          source: downloadForm.source === 'local' ? 'akshare' : downloadForm.source
        }
        
        const response = await axios.post('/api/v1/data/download', requestData)
        
        downloadTaskId.value = response.data.task_id
        showStatusDialog.value = true
        ElMessage.success('下载任务已提交')
        
        // 初始化任务状态
        downloadTaskStatus.value = {
          status: 'running',
          progress: 0,
          message: '开始下载数据...'
        }
        
        // 订阅任务状态更新
        if (isWsConnected.value) {
          wsService.subscribeTask(downloadTaskId.value)
        } else {
          // 如果WebSocket未连接，使用轮询作为后备
          pollDownloadStatus()
        }
      } catch (error) {
        console.error('提交下载任务失败:', error)
        ElMessage.error('提交失败: ' + (error as Error).message)
      } finally {
        submitting.value = false
      }
    }
  })
}

// 轮询下载状态（作为WebSocket的后备）
const pollDownloadStatus = async () => {
  if (!downloadTaskId.value || !showStatusDialog.value || isWsConnected.value) return
  
  try {
    // 模拟状态更新（仅在WebSocket未连接时使用）
    if (!downloadTaskStatus.value) {
      downloadTaskStatus.value = {
        status: 'running',
        progress: 0,
        message: '开始下载数据...'
      }
    } else if (downloadTaskStatus.value.progress < 100) {
      downloadTaskStatus.value.progress += 5
      if (downloadTaskStatus.value.progress < 50) {
        downloadTaskStatus.value.message = `正在下载数据... ${downloadTaskStatus.value.progress}%`
      } else if (downloadTaskStatus.value.progress < 80) {
        downloadTaskStatus.value.message = `正在处理数据... ${downloadTaskStatus.value.progress}%`
      } else {
        downloadTaskStatus.value.message = `正在生成文件... ${downloadTaskStatus.value.progress}%`
      }
    } else {
      downloadTaskStatus.value.status = 'completed'
      downloadTaskStatus.value.message = '下载完成'
      
      // 添加到文件列表
      const newFile = {
        id: files.value.length + 1,
        name: `stock_data_${Date.now()}.${downloadForm.format}`,
        size: 1024 * 120,
        type: downloadForm.format,
        create_time: new Date().toLocaleString('zh-CN')
      }
      files.value.unshift(newFile)
    }
    
    // 如果任务未完成，继续轮询
    if (downloadTaskStatus.value.status === 'running') {
      setTimeout(pollDownloadStatus, 2000)
    }
  } catch (error) {
    console.error('获取下载状态失败:', error)
  }
}

// 处理WebSocket消息
const handleWebSocketMessage = (data: TaskStatusUpdate) => {
  // 只处理当前下载任务的更新
  if (data.task_id === downloadTaskId.value && showStatusDialog.value) {
    // 更新任务状态
    downloadTaskStatus.value = {
      status: data.status,
      progress: data.progress,
      message: data.result?.message || `正在下载... ${data.progress}%`
    }
    
    // 如果任务完成，刷新文件列表以获取真实的文件信息
    if (data.status === 'completed') {
      downloadTaskStatus.value.message = '下载完成'
      await refreshFiles()
    } else if (data.status === 'failed') {
      downloadTaskStatus.value.message = `下载失败: ${data.error || '未知错误'}`
      ElMessage.error(downloadTaskStatus.value.message)
    }
  }
}

// 下载结果文件
const downloadResultFile = () => {
  ElMessage.success('文件开始下载')
  // 实际项目中应该调用API下载文件
  // window.open(`/api/v1/data/download/result/${downloadTaskId.value}`)
}

// 重置下载表单
const resetDownloadForm = () => {
  downloadFormRef.value?.resetFields()
}

// 生命周期钩子
onMounted(() => {
  // 初始化WebSocket连接
  wsService.connect()
  
  // 监听连接状态
  isWsConnected.value = wsService.connected.value
  
  // 设置消息处理函数
  wsService.onMessage(handleWebSocketMessage)
  
  // 加载文件列表
  refreshFiles()
})

onUnmounted(() => {
  // 如果有活动的下载任务，取消订阅
  if (downloadTaskId.value) {
    wsService.unsubscribeTask(downloadTaskId.value)
  }
  
  // 清理WebSocket连接
  wsService.destroy()
})

// 获取文件统计信息
const getFileStats = async () => {
  try {
    const response = await axios.get('/api/v1/data/files/stats')
    if (response.data.data) {
      fileStats.value = response.data.data
    }
  } catch (error) {
    console.error('获取文件统计失败', error)
    // 如果API调用失败，根据现有文件列表计算统计信息
    calculateFileStatsLocally()
  }
}

// 本地计算文件统计信息作为降级方案
const calculateFileStatsLocally = () => {
  const stats = {
    total: files.value.length,
    csv: 0,
    excel: 0,
    parquet: 0,
    totalSize: 0
  }
  
  files.value.forEach((file: any) => {
    // 根据文件扩展名分类
    const ext = file.name.split('.').pop()?.toLowerCase() || ''
    if (ext === 'csv') {
      stats.csv++
    } else if (['xlsx', 'xls'].includes(ext)) {
      stats.excel++
    } else if (ext === 'parquet') {
      stats.parquet++
    }
    
    // 累加文件大小
    stats.totalSize += file.size || 0
  })
  
  fileStats.value = stats
}

// 刷新文件列表
const refreshFiles = async () => {
  try {
    // 调用API获取文件列表
    const response = await axios.get('/api/v1/data/files')
      files.value = response.data.data || []
     
      // 重新排序文件，将最新上传的文件放在前面
      files.value.sort((a: any, b: any) => {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      })
      
      // 获取文件统计信息
      await getFileStats()
    
    ElMessage.success('文件列表已刷新')
  } catch (error) {
    console.error('获取文件列表失败:', error)
    ElMessage.error('刷新文件列表失败')
    // 降级到本地计算统计信息
    calculateFileStatsLocally()
  }
}

// 加载文件预览数据
const loadFilePreview = async (file: any) => {
  if (!file) {
    previewData.value = []
    previewColumns.value = []
    return
  }
  
  try {
    isPreviewLoading.value = true
    // 调用API获取文件预览数据
    const response = await axios.get(`/api/v1/data/files/${file.id}/preview`)
    
    if (response.data.data && response.data.data.length > 0) {
      previewData.value = response.data.data
      // 提取列名
      previewColumns.value = Object.keys(response.data.data[0])
    } else {
      previewData.value = []
      previewColumns.value = []
      ElMessage.warning('文件数据为空')
    }
  } catch (error) {
    console.error(`加载文件预览失败: ${file.name}`, error)
    ElMessage.error('文件预览失败')
    previewData.value = []
    previewColumns.value = []
  } finally {
    isPreviewLoading.value = false
  }
}

// 监听文件选择变化，自动加载预览数据
watch(
  selectedFile,
  (newFile) =\u003e {
    loadFilePreview(newFile)
  },
  { immediate: true }
)

// 下载文件
const downloadFile = async (file: any) => {
  try {
    ElMessage.success(`开始下载文件: ${file.name}`)
    // 调用API下载文件
    window.open(`/api/v1/data/files/${file.id}/download`)
  } catch (error) {
    console.error(`下载文件失败: ${file.name}`, error)
    ElMessage.error('文件下载失败')
  }
}

// 删除文件
const deleteFile = (id: number) => {
  ElMessageBox.confirm('确定要删除此文件吗？', '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      // 调用API删除文件
      await axios.delete(`/api/v1/data/files/${id}`)
      // 从本地列表中移除
      files.value = files.value.filter(file => file.id !== id)
      ElMessage.success('文件已删除')
    } catch (error) {
      console.error(`删除文件失败: ${id}`, error)
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 导出ElMessageBox
import { ElMessageBox, ElSkeleton } from 'element-plus'

// 批量操作相关功能
const selectedFiles = ref<any[]>([])
const toggleSelectFile = (file: any, checked: boolean) => {
  const index = selectedFiles.value.findIndex(f => f.id === file.id)
  if (checked && index === -1) {
    selectedFiles.value.push(file)
  } else if (!checked && index !== -1) {
    selectedFiles.value.splice(index, 1)
  }
}

const batchDeleteFiles = async () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择要删除的文件')
    return
  }
  
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedFiles.value.length} 个文件吗？`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    // 批量删除文件
    const ids = selectedFiles.value.map(file => file.id)
    await axios.post('/api/v1/data/files/batch-delete', { ids })
    
    selectedFiles.value = []
    await refreshFiles()
    ElMessage.success('批量删除成功')
  } catch (error) {
    console.error('批量删除文件失败:', error)
    if ((error as any).message !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 检查文件是否已选中
const isFileSelected = (file: any) => {
  return selectedFiles.value.some(f => f.id === file.id)
}
</script>

<style scoped>
/* 全局容器样式 */
.data-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面标题 */
.page-title {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 24px;
  color: #303133;
  text-align: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  padding: 20px 0;
}

/* 下载表单卡片 */
.download-form {
  margin-bottom: 30px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
  transition: box-shadow 0.3s ease;
}

.download-form:hover {
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15);
}

/* 卡片头部 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 18px;
  font-weight: 600;
  padding: 15px 20px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

/* 统计容器 */
.stats-container {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 20px;
  padding: 20px;
}

/* 统计卡片 */
.stat-item {
  flex: 1;
  min-width: 150px;
  text-align: center;
  padding: 24px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  cursor: pointer;
}

.stat-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  margin-bottom: 8px;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 骨架屏 */
.preview-skeleton {
  width: 100%;
  min-height: 400px;
}

/* 日期范围选择器 */
.date-range {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 状态文本 */
.status-text {
  text-align: center;
  margin-top: 20px;
  color: #606266;
  font-size: 16px;
}

/* 无数据状态 */
.no-data {
  padding: 80px 0;
  text-align: center;
}

/* 表格样式优化 */
.el-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.08);
}

.el-table__header-wrapper {
  background: #f5f7fa;
}

.el-table th {
  background: transparent !important;
  font-weight: 600;
  color: #606266;
  font-size: 14px;
}

.el-table__row {
  transition: background-color 0.2s ease;
}

.el-table__row:hover {
  background-color: #f5f7fa !important;
}

/* 操作按钮容器 */
.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

/* 进度条样式 */
.progress-container {
  margin-top: 20px;
}

/* 对话框样式优化 */
.el-dialog {
  border-radius: 12px;
  overflow: hidden;
}

.el-dialog__header {
  background-color: #f5f7fa;
  padding: 20px 30px 15px;
  border-bottom: 1px solid #ebeef5;
}

.el-dialog__title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.el-dialog__body {
  padding: 30px;
}

/* 输入框聚焦样式 */
.el-input:focus-within .el-input__wrapper,
.el-select:focus-within .el-input__wrapper {
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

/* 按钮样式优化 */
.el-button {
  transition: all 0.3s ease;
  border-radius: 6px;
}

.el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.el-button--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

.el-button--primary:hover,
.el-button--primary:focus {
  background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* 动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.fade-in {
  animation: fadeIn 0.5s ease-out;
}

.slide-in-right {
  animation: slideInRight 0.4s ease-out;
}

/* 标签页样式 */
.el-tabs__header {
  margin-bottom: 25px;
}

.el-tabs__nav-wrap {
  padding: 0 20px;
}

.el-tabs__nav {
  height: 50px;
}

.el-tabs__item {
  font-size: 16px;
  font-weight: 500;
  padding: 0 20px;
  height: 50px;
  line-height: 50px;
  color: #606266;
  transition: all 0.3s ease;
}

.el-tabs__item:hover {
  color: #667eea;
}

.el-tabs__item.is-active {
  color: #667eea;
  font-weight: 600;
}

.el-tabs__active-bar {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  height: 3px;
  border-radius: 3px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .data-container {
    padding: 15px;
  }
  
  .stat-value {
    font-size: 28px;
  }
}

@media (max-width: 768px) {
  .data-container {
    padding: 10px;
  }
  
  .page-title {
    font-size: 24px;
    margin-bottom: 15px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
    padding: 15px;
  }
  
  .card-header > div {
    width: 100%;
    display: flex;
    justify-content: space-between;
  }
  
  .stats-container {
    flex-direction: column;
    gap: 15px;
  }
  
  .stat-item {
    min-width: auto;
  }
  
  .stat-value {
    font-size: 24px;
  }
  
  .date-range {
    flex-direction: column;
    align-items: stretch;
    gap: 0;
  }
  
  .date-range .el-date-picker {
    width: 100% !important;
    margin-bottom: 10px;
  }
  
  .date-range span {
    display: none;
  }
  
  .el-tabs__nav-wrap {
    padding: 0 10px;
  }
  
  .el-tabs__item {
    font-size: 14px;
    padding: 0 10px;
  }
  
  .el-dialog {
    width: 90% !important;
    margin: 5% auto;
  }
  
  .el-dialog__body {
    padding: 20px;
  }
}

@media (max-width: 480px) {
  .data-container {
    padding: 5px;
  }
  
  .page-title {
    font-size: 20px;
  }
  
  .stat-item {
    padding: 15px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .stat-label {
    font-size: 12px;
  }
}
</style>
