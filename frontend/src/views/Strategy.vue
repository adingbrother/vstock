<template>
  <div class="strategy-container">
    <h2>策略管理</h2>
    
    <!-- 搜索和筛选 -->
    <el-card class="mb-4">
      <div class="search-filter">
        <el-input
          v-model="searchQuery"
          placeholder="搜索策略名称或描述"
          prefix-icon="Search"
          clearable
          class="search-input"
          @input="handleSearch"
        ></el-input>
        <el-select v-model="filterStatus" placeholder="状态筛选" clearable @change="handleSearch">
          <el-option label="全部" value=""></el-option>
          <el-option label="已启用" value="enabled"></el-option>
          <el-option label="已禁用" value="disabled"></el-option>
        </el-select>
        <el-button type="primary" @click="showCreateForm = true">
          <el-icon><Plus /></el-icon>
          创建新策略
        </el-button>
      </div>
    </el-card>
    
    <!-- 策略列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>已保存的策略</span>
          <span class="total-count">共 {{ strategies.length }} 个策略</span>
        </div>
      </template>
      
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="5" animated />
      </div>
      
      <el-table v-else-if="filteredStrategies.length > 0" :data="filteredStrategies" stripe>
        <el-table-column prop="id" label="ID" width="80"></el-table-column>
        <el-table-column prop="name" label="策略名称" show-overflow-tooltip>
          <template #default="scope">
            <div class="strategy-name">
              <span>{{ scope.row.name }}</span>
              <el-tag v-if="scope.row.is_default" type="success" size="small" class="ml-2">默认</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip></el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-switch
              v-model="scope.row.status"
              active-value="enabled"
              inactive-value="disabled"
              @change="handleStatusChange(scope.row)"
              :disabled="scope.row.is_default"
            ></el-switch>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180"></el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180"></el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="editStrategy(scope.row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteStrategy(scope.row)"
              :disabled="scope.row.is_default"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-else class="empty-state">
        <el-empty description="暂无策略数据" />
      </div>
    </el-card>
    
    <!-- 创建/编辑策略表单 -->
    <el-dialog v-model="showCreateForm" :title="editingStrategy ? '编辑策略' : '创建新策略'" width="800px">
      <el-form ref="strategyFormRef" :model="strategyForm" :rules="rules" label-width="80px">
        <el-form-item label="策略名称" prop="name">
          <el-input v-model="strategyForm.name" placeholder="请输入策略名称"></el-input>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="strategyForm.description" type="textarea" placeholder="请输入策略描述" :rows="2"></el-input>
        </el-form-item>
        <el-form-item label="策略参数" prop="params" class="mb-0">
          <el-button type="text" @click="showParamsConfig = true">配置策略参数</el-button>
          <div v-if="Object.keys(strategyParams).length > 0" class="params-preview">
            <el-tag v-for="(value, key) in strategyParams" :key="key" size="small" class="m-1">
              {{ key }}: {{ value }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="策略代码" prop="code">
          <el-input v-model="strategyForm.code" type="textarea" :rows="12" placeholder="请输入策略代码" spellcheck="false"></el-input>
          <div class="code-hint mt-2">
            <el-alert
              title="提示"
              :description="'策略函数必须名为strategy，接收data和params参数，并返回交易信号序列。'"
              type="info"
              show-icon
              :closable="false"
            ></el-alert>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cancelSave">取消</el-button>
        <el-button type="primary" @click="saveStrategy" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
    
    <!-- 参数配置对话框 -->
    <el-dialog v-model="showParamsConfig" title="配置策略参数" width="500px">
      <el-form :model="strategyParams" label-width="100px">
        <el-form-item v-for="(param, index) in paramsList" :key="index" :label="param.key" :prop="param.key">
          <el-input v-model="strategyParams[param.key]" :placeholder="`请输入${param.key}`"></el-input>
          <el-button type="text" @click="removeParam(index)" v-if="paramsList.length > 1">删除</el-button>
        </el-form-item>
        <el-button type="dashed" @click="addParam" class="w-full">添加参数</el-button>
      </el-form>
      <template #footer>
        <el-button @click="showParamsConfig = false">取消</el-button>
        <el-button type="primary" @click="confirmParams">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElForm } from 'element-plus'
import { Plus, Edit, Delete, Search } from '@element-plus/icons-vue'
import axios from 'axios'

const strategyFormRef = ref<InstanceType<typeof ElForm> | null>(null)
const showCreateForm = ref(false)
const showParamsConfig = ref(false)
const editingStrategy = ref<any>(null)
const loading = ref(false)
const saving = ref(false)
const searchQuery = ref('')
const filterStatus = ref('')

// 策略表单数据
const strategyForm = reactive({
  name: '',
  description: '',
  code: `def strategy(data, params):\n    # 简单的均线策略示例\n    import pandas as pd\n    import numpy as np\n    \n    # 计算5日均线和20日均线\n    data['ma5'] = data['close'].rolling(window=5).mean()\n    data['ma20'] = data['close'].rolling(window=20).mean()\n    \n    # 生成交易信号\n    data['signal'] = 0\n    data.loc[data['ma5'] > data['ma20'], 'signal'] = 1  # 买入信号\n    data.loc[data['ma5'] < data['ma20'], 'signal'] = 0  # 卖出信号\n    \n    return data['signal']`,
  params: {}
})

// 策略参数配置
const strategyParams = reactive<Record<string, any>>({
  // 默认参数示例
  short_window: 5,
  long_window: 20
})

const paramsList = ref([
  { key: 'short_window', value: 5 },
  { key: 'long_window', value: 20 }
])

// 表单验证规则
const rules = reactive({
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' },
    { min: 2, max: 50, message: '策略名称长度在 2 到 50 个字符', trigger: 'blur' },
    { validator: validateNameUnique, trigger: 'blur' }
  ],
  description: [
    { max: 200, message: '描述长度不能超过200个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入策略代码', trigger: 'blur' },
    { min: 20, message: '策略代码不能少于20个字符', trigger: 'blur' },
    { pattern: /def\s+strategy\s*\([^)]*\)/, message: '必须包含strategy函数定义', trigger: 'blur' }
  ]
})

// 策略列表
const strategies = ref([
  // 模拟数据
  {
    id: 1,
    name: '均线策略',
    description: '基于5日和20日均线交叉的交易策略',
    status: 'enabled',
    is_default: true,
    created_at: '2023-01-01 10:00:00',
    updated_at: '2023-01-01 10:00:00'
  },
  {
    id: 2,
    name: 'MACD策略',
    description: '基于MACD指标的交易策略',
    status: 'enabled',
    is_default: false,
    created_at: '2023-01-02 14:30:00',
    updated_at: '2023-01-02 14:30:00'
  },
  {
    id: 3,
    name: 'RSI策略',
    description: '基于相对强弱指标的交易策略',
    status: 'disabled',
    is_default: false,
    created_at: '2023-01-03 09:15:00',
    updated_at: '2023-01-03 09:15:00'
  }
])

// 筛选后的策略列表
const filteredStrategies = computed(() => {
  return strategies.value.filter(strategy => {
    // 搜索筛选
    const searchMatch = !searchQuery.value || 
      strategy.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      strategy.description.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    // 状态筛选
    const statusMatch = !filterStatus.value || strategy.status === filterStatus.value
    
    return searchMatch && statusMatch
  })
})

// 验证策略名称唯一性
const validateNameUnique = (rule: any, value: string, callback: Function) => {
  const exists = strategies.value.some(strategy => {
    return strategy.name === value && (!editingStrategy.value || strategy.id !== editingStrategy.value.id)
  })
  
  if (exists) {
    callback(new Error('策略名称已存在'))
  } else {
    callback()
  }
}

// 初始化加载策略列表
const loadStrategies = async () => {
  loading.value = true
  try {
    // 模拟API调用
    // const response = await axios.get('/api/v1/strategies')
    // strategies.value = response.data
    
    // 模拟延迟
    await new Promise(resolve => setTimeout(resolve, 500))
    console.log('策略列表加载完成')
  } catch (error) {
    console.error('加载策略失败:', error)
    ElMessage.error('加载策略失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 处理搜索
const handleSearch = () => {
  // 搜索逻辑已经在计算属性中实现
  console.log('搜索查询:', searchQuery.value, '状态筛选:', filterStatus.value)
}

// 添加参数
const addParam = () => {
  const newKey = `param_${Date.now()}`
  paramsList.value.push({ key: newKey, value: '' })
  strategyParams[newKey] = ''
}

// 移除参数
const removeParam = (index: number) => {
  const param = paramsList.value[index]
  delete strategyParams[param.key]
  paramsList.value.splice(index, 1)
}

// 确认参数配置
const confirmParams = () => {
  // 更新策略表单中的参数
  strategyForm.params = { ...strategyParams }
  showParamsConfig.value = false
}

// 编辑策略
const editStrategy = (strategy: any) => {
  editingStrategy.value = strategy
  strategyForm.name = strategy.name
  strategyForm.description = strategy.description
  strategyForm.params = strategy.params || {}
  
  // 初始化参数配置
  Object.keys(strategyParams).forEach(key => {
    delete strategyParams[key]
  })
  paramsList.value = []
  
  // 如果策略有参数，加载参数
  if (strategy.params) {
    Object.entries(strategy.params).forEach(([key, value]) => {
      strategyParams[key] = value
      paramsList.value.push({ key, value })
    })
  } else {
    // 设置默认参数
    strategyParams.short_window = 5
    strategyParams.long_window = 20
    paramsList.value = [
      { key: 'short_window', value: 5 },
      { key: 'long_window', value: 20 }
    ]
  }
  
  // 策略代码（实际项目中应该从API获取）
  strategyForm.code = getStrategyCodeByType(strategy.name)
  showCreateForm.value = true
}

// 根据策略类型获取代码模板
const getStrategyCodeByType = (name: string): string => {
  if (name.includes('MACD')) {
    return `def strategy(data, params):\n    import pandas as pd\n    import numpy as np\n    \n    # MACD计算\n    exp1 = data['close'].ewm(span=12, adjust=False).mean()\n    exp2 = data['close'].ewm(span=26, adjust=False).mean()\n    data['macd'] = exp1 - exp2\n    data['signal_line'] = data['macd'].ewm(span=9, adjust=False).mean()\n    \n    # 生成信号\n    data['signal'] = 0\n    data.loc[data['macd'] > data['signal_line'], 'signal'] = 1\n    data.loc[data['macd'] < data['signal_line'], 'signal'] = 0\n    \n    return data['signal']`
  } else if (name.includes('RSI')) {
    return `def strategy(data, params):\n    import pandas as pd\n    import numpy as np\n    \n    # 计算RSI\n    delta = data['close'].diff()\n    gain = delta.where(delta > 0, 0)\n    loss = -delta.where(delta < 0, 0)\n    avg_gain = gain.rolling(window=14).mean()\n    avg_loss = loss.rolling(window=14).mean()\n    \n    rs = avg_gain / avg_loss\n    data['rsi'] = 100 - (100 / (1 + rs))\n    \n    # 生成信号\n    data['signal'] = 0\n    data.loc[data['rsi'] < 30, 'signal'] = 1  # 超卖买入\n    data.loc[data['rsi'] > 70, 'signal'] = 0  # 超买卖出\n    \n    return data['signal']`
  } else {
    // 默认均线策略
    return `def strategy(data, params):\n    # 简单的均线策略示例\n    import pandas as pd\n    import numpy as np\n    \n    # 计算均线\n    short_window = params.get('short_window', 5)\n    long_window = params.get('long_window', 20)\n    \n    data['short_ma'] = data['close'].rolling(window=short_window).mean()\n    data['long_ma'] = data['close'].rolling(window=long_window).mean()\n    \n    # 生成交易信号\n    data['signal'] = 0\n    data.loc[data['short_ma'] > data['long_ma'], 'signal'] = 1  # 买入信号\n    data.loc[data['short_ma'] < data['long_ma'], 'signal'] = 0  # 卖出信号\n    \n    return data['signal']`
  }
}

// 保存策略
const saveStrategy = async () => {
  if (!strategyFormRef.value) return
  
  await strategyFormRef.value.validate(async (valid) => {
    if (valid) {
      saving.value = true
      try {
        // 合并参数
        strategyForm.params = { ...strategyParams }
        
        if (editingStrategy.value) {
          // 更新策略
          // await axios.put(`/api/v1/strategies/${editingStrategy.value.id}`, strategyForm)
          const index = strategies.value.findIndex(s => s.id === editingStrategy.value.id)
          if (index !== -1) {
            strategies.value[index] = {
              ...strategies.value[index],
              name: strategyForm.name,
              description: strategyForm.description,
              params: strategyForm.params,
              updated_at: new Date().toLocaleString()
            }
          }
          ElMessage.success('策略更新成功')
        } else {
          // 创建策略
          // const response = await axios.post('/api/v1/strategies', strategyForm)
          const newStrategy = {
            id: Date.now(), // 临时ID，实际应由后端生成
            name: strategyForm.name,
            description: strategyForm.description,
            params: strategyForm.params,
            status: 'enabled',
            is_default: false,
            created_at: new Date().toLocaleString(),
            updated_at: new Date().toLocaleString()
          }
          strategies.value.unshift(newStrategy)
          ElMessage.success('策略创建成功')
        }
        
        // 关闭对话框并重置表单
        cancelSave()
      } catch (error) {
        console.error('保存策略失败:', error)
        ElMessage.error('保存失败: ' + (error as Error).message)
      } finally {
        saving.value = false
      }
    }
  })
}

// 取消保存
const cancelSave = () => {
  showCreateForm.value = false
  resetForm()
}

// 处理状态变更
const handleStatusChange = async (strategy: any) => {
  try {
    // 模拟API调用
    // await axios.patch(`/api/v1/strategies/${strategy.id}/status`, { status: strategy.status })
    console.log('更新策略状态:', strategy.id, strategy.status)
    ElMessage.success('状态更新成功')
  } catch (error) {
    // 恢复原状态
    strategy.status = strategy.status === 'enabled' ? 'disabled' : 'enabled'
    console.error('更新状态失败:', error)
    ElMessage.error('状态更新失败')
  }
}

// 删除策略
const deleteStrategy = async (strategy: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除策略「${strategy.name}」吗？此操作不可恢复。`, 
      '确认删除', 
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 实际项目中应该调用API
    // await axios.delete(`/api/v1/strategies/${strategy.id}`)
    strategies.value = strategies.value.filter(s => s.id !== strategy.id)
    ElMessage.success('策略删除成功')
  } catch (error) {
    // 用户取消删除不会触发错误
  }
}

// 重置表单
const resetForm = () => {
  strategyFormRef.value?.resetFields()
  editingStrategy.value = null
  
  // 重置参数配置
  Object.keys(strategyParams).forEach(key => {
    delete strategyParams[key]
  })
  strategyParams.short_window = 5
  strategyParams.long_window = 20
  paramsList.value = [
    { key: 'short_window', value: 5 },
    { key: 'long_window', value: 20 }
  ]
}

// 组件挂载时加载策略列表
onMounted(() => {
  loadStrategies()
})
</script>

<style scoped>
.strategy-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-filter {
  display: flex;
  gap: 16px;
  align-items: center;
}

.search-input {
  width: 300px;
}

.mb-4 {
  margin-bottom: 16px;
}

.total-count {
  color: #606266;
  font-size: 14px;
}

.loading-container {
  padding: 20px 0;
}

.empty-state {
  padding: 40px 0;
}

.strategy-name {
  display: flex;
  align-items: center;
}

.ml-2 {
  margin-left: 8px;
}

.params-preview {
  margin-top: 10px;
  flex-wrap: wrap;
}

.code-hint {
  margin-top: 10px;
}
</style>