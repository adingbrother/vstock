<template>
  <div class="settings-container">
    <h2 class="page-title">系统设置</h2>
    <el-tabs v-model="activeTab" type="border-card"
      :tab-position="isMobile ? 'top' : 'left'"
    >
      <el-tab-pane label="基本设置">
        <el-card class="settings-card">
          <el-form ref="basicFormRef" :model="basicSettings" label-width="150px"
            :rules="basicFormRules"
          >
            <el-form-item label="平台名称" prop="platform_name">
              <el-input v-model="basicSettings.platform_name" placeholder="请输入平台名称"></el-input>
            </el-form-item>
            <el-form-item label="默认语言" prop="language">
              <el-select v-model="basicSettings.language" placeholder="请选择默认语言">
                <el-option label="简体中文" value="zh-CN"></el-option>
                <el-option label="English" value="en-US"></el-option>
              <el-select>
            </el-form-item>
            <el-form-item label="主题颜色" prop="theme_color">
              <el-color-picker v-model="basicSettings.theme_color"
                show-alpha
                :predefine="predefineColors"
              ></el-color-picker>
            </el-form-item>
            <el-form-item label="数据刷新间隔">
              <el-input-number
                v-model="basicSettings.refresh_interval"
                :min="5"
                :max="300"
                :step="5"
                placeholder="数据刷新间隔（秒）"
              ></el-input-number>
              <div class="form-hint">数据看板和任务列表的自动刷新间隔时间（秒）</div>
            </el-form-item>
            <el-form-item label="自动保存设置">
              <el-switch v-model="basicSettings.auto_save"
                active-text="启用"
                inactive-text="禁用"
              ></el-switch>
            </el-form-item>
            <el-form-item label="操作日志级别">
              <el-select v-model="basicSettings.log_level" placeholder="请选择日志级别">
                <el-option label="DEBUG" value="debug"></el-option>
                <el-option label="INFO" value="info"></el-option>
                <el-option label="WARNING" value="warning"></el-option>
                <el-option label="ERROR" value="error"></el-option>
              <el-select>
            </el-form-item>
            <el-form-item label="显示高级选项">
              <el-switch v-model="showAdvancedOptions"
                active-text="显示"
                inactive-text="隐藏"
              ></el-switch>
            </el-form-item>
            <el-form-item v-if="showAdvancedOptions" label="最大并发任务数">
              <el-input-number
                v-model="basicSettings.max_concurrent_tasks"
                :min="1"
                :max="10"
                placeholder="最大并发任务数"
              ></el-input-number>
            </el-form-item>
            <el-form-item v-if="showAdvancedOptions" label="任务超时时间（分钟）">
              <el-input-number
                v-model="basicSettings.task_timeout"
                :min="5"
                :max="1440"
                placeholder="任务超时时间"
              ></el-input-number>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveBasicSettings"
                :loading="savingBasic"
              >保存基本设置</el-button>
              <el-button @click="resetBasicSettings">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="数据源设置">
        <el-card class="settings-card">
          <template #header>
            <div class="card-header">
              <span>数据源配置管理</span>
              <el-button type="primary" size="small" @click="showAddDataSource = true">
                <el-icon><Plus /></el-icon> 添加数据源
              </el-button>
            </div>
          </template>
          <el-table :data="dataSources" stripe style="width: 100%"
            v-loading="loadingDataSources"
          >
            <el-table-column prop="name" label="数据源名称" />
            <el-table-column prop="type" label="类型" formatter="formatDataSourceType" />
            <el-table-column prop="url" label="连接地址" show-overflow-tooltip />
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="is_active" label="状态"
              formatter="formatDataSourceStatus"
            >
              <template #default="scope">
                <el-tag
                  :type="scope.row.is_active ? 'success' : 'danger'"
                  effect="dark"
                >{{ scope.row.is_active ? '启用' : '禁用' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" />
            <el-table-column label="操作" width="180"
              fixed="right"
            >
              <template #default="scope">
                <el-button size="small" type="primary"
                  @click="editDataSource(scope.row)"
                >编辑</el-button>
                <el-button size="small" type="info"
                  @click="testDataSource(scope.row)"
                >测试连接<el-button>
                <el-button size="small" type="danger"
                  @click="deleteDataSource(scope.row.id)"
                >删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="API设置">
        <el-card class="settings-card">
          <el-form ref="apiFormRef" :model="apiSettings" label-width="150px"
            :rules="apiFormRules"
          >
            <el-form-item label="API基础URL" prop="api_base_url">
              <el-input v-model="apiSettings.api_base_url" placeholder="请输入API基础URL"></el-input>
              <div class="form-hint">例如：http://localhost:8000/api/v1/</div>
            </el-form-item>
            <el-form-item label="请求超时时间">
              <el-input-number
                v-model="apiSettings.timeout"
                :min="5000"
                :max="60000"
                :step="1000"
                placeholder="超时时间（毫秒）"
              ></el-input-number>
            </el-form-item>
            <el-form-item label="最大重试次数">
              <el-input-number
                v-model="apiSettings.max_retries"
                :min="0"
                :max="5"
                placeholder="最大重试次数"
              ></el-input-number>
            </el-form-item>
            <el-form-item label="启用CORS">
              <el-switch v-model="apiSettings.enable_cors"
                active-text="启用"
                inactive-text="禁用"
              ></el-switch>
            </el-form-item>
            <el-form-item label="认证令牌" prop="auth_token"
              v-if="showAuthToken"
            >
              <el-input
                v-model="apiSettings.auth_token"
                type="password"
                placeholder="请输入认证令牌"
                show-password
              ></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveApiSettings"
                :loading="savingApi"
              >保存API设置</el-button>
              <el-button @click="resetApiSettings">重置</el-button>
              <el-button type="info" @click="testApiConnection"
                :loading="testingApi"
              >测试连接</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
      <el-tab-pane label="关于系统">
        <el-card class="about-card"
          :body-style="{ padding: '40px 0', textAlign: 'center' }"
        >
          <div class="system-logo"
            :style="{ backgroundColor: basicSettings.theme_color }"
          >
            <span class="logo-text">QuantWeb</span>
          </div>
          <h2 class="system-name" style="margin-top: 30px">量化投研平台</h2>
          <p class="system-version">版本号: {{ systemInfo.version }}</p>
          <p class="system-description">{{ systemInfo.description }}</p>
          <div class="system-info"
            style="margin-top: 40px; text-align: left; padding: 0 40px"
          >
            <h3 style="margin-bottom: 20px; color: #303133">系统信息</h3>
            <el-descriptions :column="isMobile ? 1 : 2" border :size="isMobile ? 'large' : 'default'"
              :title="''"
            >
              <el-descriptions-item label="前端框架">{{ systemInfo.frontend_framework }}</el-descriptions-item>
              <el-descriptions-item label="后端框架">{{ systemInfo.backend_framework }}</el-descriptions-item>
              <el-descriptions-item label="构建日期">{{ systemInfo.build_date }}</el-descriptions-item>
              <el-descriptions-item label="运行环境">{{ systemInfo.environment }}</el-descriptions-item>
              <el-descriptions-item label="浏览器版本">{{ systemInfo.browser }}</el-descriptions-item>
              <el-descriptions-item label="开发者">{{ systemInfo.developer }}</el-descriptions-item>
            </el-descriptions>
          </div>
          <div class="system-actions" style="margin-top: 40px">
            <el-button type="primary" @click="checkUpdate"
              :loading="checkingUpdate"
            >检查更新</el-button>
            <el-button @click="exportSettings">导出设置</el-button>
            <el-button type="warning" @click="clearCache">清除缓存</el-button>
          </div>
        </el-card>
      </el-tab-pane>
    </el-tabs>
    <!-- 添加/编辑数据源对话框 -->
    <el-dialog
      v-model="showAddDataSource"
      :title="editingDataSource ? '编辑数据源' : '添加数据源'"
      width="500px"
    >
      <el-form ref="dataSourceFormRef" :model="dataSourceForm" label-width="120px"
        :rules="dataSourceFormRules"
      >
        <el-form-item label="数据源名称" prop="name">
          <el-input v-model="dataSourceForm.name" placeholder="请输入数据源名称"></el-input>
        </el-form-item>
        <el-form-item label="数据源类型" prop="type">
          <el-select v-model="dataSourceForm.type" placeholder="请选择数据源类型">
            <el-option label="本地数据库" value="local_db"></el-option>
            <el-option label="公开API" value="public_api"></el-option>
            <el-option label="自定义API" value="custom_api"></el-option>
          <el-select>
        </el-form-item>
        <el-form-item label="连接地址" prop="url">
          <el-input v-model="dataSourceForm.url" placeholder="请输入连接地址"></el-input>
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="dataSourceForm.username" placeholder="请输入用户名"></el-input>
        </el-form-item>
        <el-form-item label="密码" prop="password"
          v-if="dataSourceForm.type !== 'public_api'"
        >
          <el-input
            v-model="dataSourceForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
          ></el-input>
        </el-form-item>
        <el-form-item label="是否启用">
          <el-switch v-model="dataSourceForm.is_active"
            active-text="启用"
            inactive-text="禁用"
          ></el-switch>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="closeDataSourceDialog">取消</el-button>
        <el-button type="primary" @click="saveDataSource"
          :loading="savingDataSource"
        >保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElForm, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import axios from 'axios'

const activeTab = ref('0')
const basicFormRef = ref<InstanceType<typeof ElForm> | null>(null)
const apiFormRef = ref<InstanceType<typeof ElForm> | null>(null)
const dataSourceFormRef = ref<InstanceType<typeof ElForm> | null>(null)

// 响应式判断是否为移动端
const isMobile = computed(() => {
  return window.innerWidth < 768
})

// 预定义颜色
const predefineColors = ref([
  '#409EFF',
  '#67C23A',
  '#E6A23C',
  '#F56C6C',
  '#909399',
  '#1890FF',
  '#52C41A',
  '#FA8C16',
  '#F5222D',
  '#722ED1'
])

// 状态变量
const showAdvancedOptions = ref(false)
const showAuthToken = ref(false)
const showAddDataSource = ref(false)
const editingDataSource = ref(false)

// 加载状态
const savingBasic = ref(false)
const savingApi = ref(false)
const testingApi = ref(false)
const checkingUpdate = ref(false)
const loadingDataSources = ref(false)
const savingDataSource = ref(false)

// 基本设置表单数据
const basicSettings = reactive({
  platform_name: '量化投研平台',
  language: 'zh-CN',
  theme_color: '#409EFF',
  refresh_interval: 30,
  auto_save: true,
  log_level: 'info',
  max_concurrent_tasks: 3,
  task_timeout: 60
})

// API设置表单数据
const apiSettings = reactive({
  api_base_url: 'http://localhost:8000/api/v1/',
  timeout: 10000,
  max_retries: 3,
  enable_cors: true,
  auth_token: ''
})

// 数据源表单数据
const dataSourceForm = reactive({
  id: null,
  name: '',
  type: 'local_db',
  url: '',
  username: '',
  password: '',
  is_active: true
})

// 模拟数据源数据
const dataSources = ref([
  {
    id: 1,
    name: '本地数据库',
    type: 'local_db',
    url: 'sqlite:///data/stock.db',
    username: 'admin',
    password: '******',
    is_active: true,
    created_at: '2024-07-10 10:00:00'
  },
  {
    id: 2,
    name: '公开股票API',
    type: 'public_api',
    url: 'https://api.example.com/stock',
    username: '',
    is_active: true,
    created_at: '2024-07-10 11:30:00'
  },
  {
    id: 3,
    name: '自定义数据源',
    type: 'custom_api',
    url: 'http://localhost:8080/api',
    username: 'user',
    password: '******',
    is_active: false,
    created_at: '2024-07-11 09:15:00'
  }
])

// 系统信息
const systemInfo = reactive({
  version: '1.0.0',
  description: '专业量化策略回测与研究平台',
  frontend_framework: 'Vue 3 + TypeScript',
  backend_framework: 'FastAPI + Python',
  build_date: '2024-07-12',
  environment: 'development',
  browser: navigator.userAgent,
  developer: 'QuantWeb Team'
})

// 表单验证规则
const basicFormRules = reactive({
  platform_name: [
    { required: true, message: '请输入平台名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  language: [
    { required: true, message: '请选择默认语言', trigger: 'change' }
  ],
  theme_color: [
    { required: true, message: '请选择主题颜色', trigger: 'change' }
  ]
})

const apiFormRules = reactive({
  api_base_url: [
    { required: true, message: '请输入API基础URL', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL', trigger: 'blur' }
  ]
})

const dataSourceFormRules = reactive({
  name: [
    { required: true, message: '请输入数据源名称', trigger: 'blur' },
    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择数据源类型', trigger: 'change' }
  ],
  url: [
    { required: true, message: '请输入连接地址', trigger: 'blur' }
  ]
})

// 格式化数据源类型
const formatDataSourceType = (type: string) => {
  const typeMap: Record<string, string> = {
    'local_db': '本地数据库',
    'public_api': '公开API',
    'custom_api': '自定义API'
  }
  return typeMap[type] || type
}

// 格式化数据源状态
const formatDataSourceStatus = (status: boolean) => {
  return status ? '启用' : '禁用'
}

// 保存基本设置
const saveBasicSettings = async () => {
  if (!basicFormRef.value) return
  
  await basicFormRef.value.validate(async (valid) => {
    if (valid) {
      savingBasic.value = true
      try {
        // 实际项目中应该调用API保存设置
        // await axios.post('/api/v1/settings/basic', basicSettings)
        
        // 保存到本地存储
        localStorage.setItem('basicSettings', JSON.stringify(basicSettings))
        
        ElMessage.success('基本设置已保存')
        
        // 应用主题颜色
        document.documentElement.style.setProperty('--el-color-primary', basicSettings.theme_color)
      } catch (error) {
        ElMessage.error('保存失败: ' + (error as Error).message)
      } finally {
        savingBasic.value = false
      }
    }
  })
}

// 重置基本设置
const resetBasicSettings = () => {
  if (!basicFormRef.value) return
  basicFormRef.value.resetFields()
}

// 保存API设置
const saveApiSettings = async () => {
  if (!apiFormRef.value) return
  
  await apiFormRef.value.validate(async (valid) => {
    if (valid) {
      savingApi.value = true
      try {
        // 实际项目中应该调用API保存设置
        // await axios.post('/api/v1/settings/api', apiSettings)
        
        // 保存到本地存储
        localStorage.setItem('apiSettings', JSON.stringify(apiSettings))
        
        ElMessage.success('API设置已保存')
      } catch (error) {
        ElMessage.error('保存失败: ' + (error as Error).message)
      } finally {
        savingApi.value = false
      }
    }
  })
}

// 重置API设置
const resetApiSettings = () => {
  if (!apiFormRef.value) return
  apiFormRef.value.resetFields()
}

// 测试API连接
const testApiConnection = async () => {
  testingApi.value = true
  try {
    // 测试健康检查接口
    const response = await axios.get(`${apiSettings.api_base_url}health`, {
      timeout: apiSettings.timeout
    })
    
    if (response.status === 200) {
      ElMessage.success('API连接成功！')
    }
  } catch (error) {
    ElMessage.error('API连接失败: ' + (error as Error).message)
  } finally {
    testingApi.value = false
  }
}

// 编辑数据源
const editDataSource = (dataSource: any) => {
  editingDataSource.value = true
  Object.assign(dataSourceForm, {
    ...dataSource,
    password: '' // 不显示密码
  })
  showAddDataSource.value = true
}

// 保存数据源
const saveDataSource = async () => {
  if (!dataSourceFormRef.value) return
  
  await dataSourceFormRef.value.validate(async (valid) => {
    if (valid) {
      savingDataSource.value = true
      try {
        if (editingDataSource.value) {
          // 编辑现有数据源
          const index = dataSources.value.findIndex(ds => ds.id === dataSourceForm.id)
          if (index !== -1) {
            dataSources.value[index] = {
              ...dataSources.value[index],
              ...dataSourceForm,
              password: dataSourceForm.password ? '******' : dataSources.value[index].password
            }
          }
        } else {
          // 添加新数据源
          const newDataSource = {
            ...dataSourceForm,
            id: Date.now(),
            password: dataSourceForm.password ? '******' : '',
            created_at: new Date().toLocaleString('zh-CN')
          }
          dataSources.value.push(newDataSource)
        }
        
        ElMessage.success('数据源配置已保存')
        closeDataSourceDialog()
      } catch (error) {
        ElMessage.error('保存失败: ' + (error as Error).message)
      } finally {
        savingDataSource.value = false
      }
    }
  })
}

// 关闭数据源对话框
const closeDataSourceDialog = () => {
  showAddDataSource.value = false
  editingDataSource.value = false
  dataSourceFormRef.value?.resetFields()
  Object.assign(dataSourceForm, {
    id: null,
    name: '',
    type: 'local_db',
    url: '',
    username: '',
    password: '',
    is_active: true
  })
}

// 删除数据源
const deleteDataSource = (id: number) => {
  ElMessageBox.confirm('确定要删除此数据源吗？', '删除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      dataSources.value = dataSources.value.filter(ds => ds.id !== id)
      ElMessage.success('数据源已删除')
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 测试数据源连接
const testDataSource = (dataSource: any) => {
  // 模拟测试连接
  ElMessage.success(`数据源 "${dataSource.name}" 连接测试成功！`)
}

// 检查更新
const checkUpdate = async () => {
  checkingUpdate.value = true
  try {
    // 模拟检查更新
    setTimeout(() => {
      ElMessage.success('当前已是最新版本')
      checkingUpdate.value = false
    }, 1000)
  } catch (error) {
    ElMessage.error('检查更新失败')
    checkingUpdate.value = false
  }
}

// 导出设置
const exportSettings = () => {
  const settings = {
    basic: basicSettings,
    api: apiSettings,
    dataSources: dataSources.value
  }
  
  const dataStr = JSON.stringify(settings, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = `quantweb_settings_${new Date().toISOString().split('T')[0]}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('设置已导出')
}

// 清除缓存
const clearCache = () => {
  ElMessageBox.confirm('确定要清除所有缓存数据吗？', '清除确认', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    localStorage.clear()
    sessionStorage.clear()
    ElMessage.success('缓存已清除，请刷新页面')
  }).catch(() => {})
}

// 从本地存储加载设置
onMounted(() => {
  try {
    const savedBasic = localStorage.getItem('basicSettings')
    if (savedBasic) {
      Object.assign(basicSettings, JSON.parse(savedBasic))
    }
    
    const savedApi = localStorage.getItem('apiSettings')
    if (savedApi) {
      Object.assign(apiSettings, JSON.parse(savedApi))
    }
    
    // 应用主题颜色
    document.documentElement.style.setProperty('--el-color-primary', basicSettings.theme_color)
  } catch (error) {
    console.error('加载本地设置失败:', error)
  }
})
</script>

<style scoped>
.settings-container {
  padding: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
  color: #303133;
}

.settings-card,
.about-card {
  margin-bottom: 30px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 500;
}

.form-hint {
  color: #909399;
  font-size: 12px;
  margin-top: 5px;
}

.system-logo {
  width: 100px;
  height: 100px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.logo-text {
  font-size: 24px;
  font-weight: 700;
  color: white;
}

.system-name {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.system-version {
  color: #409eff;
  font-size: 16px;
  margin: 10px 0;
}

.system-description {
  color: #606266;
  font-size: 14px;
}

.system-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .system-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .system-actions .el-button {
    width: 80%;
  }
  
  .el-tabs--left .el-tabs__content {
    padding-left: 10px;
  }
}
</style>
