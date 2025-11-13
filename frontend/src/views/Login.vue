<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, ElForm, ElInput, ElButton } from 'element-plus'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { Lock, User, Eye, EyeOff } from '@element-plus/icons-vue'

const router = useRouter()
const loginFormRef = ref<InstanceType<typeof ElForm> | null>(null)
const loginForm = reactive({
  username: '',
  password: ''
})

const loading = ref(false)
const showPassword = ref(false)
const rememberMe = ref(false)

// 表单验证规则
const rules = reactive({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ]
})

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        // 模拟登录API调用
        // const response = await axios.post('/api/auth/login', loginForm)
        // localStorage.setItem('token', response.data.token)
        
        // 模拟登录延迟
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // 模拟成功登录逻辑
        const mockUserInfo = {
          token: 'mock-token-' + Date.now(),
          user: {
            id: 1,
            username: loginForm.username,
            role: 'admin',
            permissions: ['read', 'write', 'execute']
          }
        }
        
        // 保存登录信息
        localStorage.setItem('token', mockUserInfo.token)
        localStorage.setItem('userInfo', JSON.stringify(mockUserInfo.user))
        
        // 如果记住我，保存到本地存储
        if (rememberMe.value) {
          localStorage.setItem('rememberedUsername', loginForm.username)
        } else {
          localStorage.removeItem('rememberedUsername')
        }
        
        ElMessage.success('登录成功，正在跳转到首页...')
        
        // 重定向到主页
        setTimeout(() => {
          router.push('/')
        }, 1000)
      } catch (error) {
        console.error('登录失败:', error)
        ElMessage.error('登录失败: 用户名或密码错误')
      } finally {
        loading.value = false
      }
    }
  })
}

// 切换密码显示状态
const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
}

// 初始化时检查是否有记住的用户名
const initForm = () => {
  const rememberedUsername = localStorage.getItem('rememberedUsername')
  if (rememberedUsername) {
    loginForm.username = rememberedUsername
    rememberMe.value = true
  }
}

// 页面加载时初始化表单
initForm()
</script>

<template>
  <div class="login-container">
    <div class="login-wrapper">
      <div class="login-form">
        <div class="login-header">
          <h1 class="login-title">策略回测系统</h1>
          <p class="login-subtitle">高效、专业的量化交易平台</p>
        </div>
        
        <el-form 
          ref="loginFormRef" 
          :model="loginForm" 
          :rules="rules"
          label-width="80px" 
          class="form-container"
        >
          <el-form-item label="用户名" prop="username">
            <el-input 
              v-model="loginForm.username" 
              placeholder="请输入用户名"
              prefix-icon="User"
              clearable
            >
              <template #prefix>
                <el-icon><User /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item label="密码" prop="password">
            <el-input 
              v-model="loginForm.password" 
              :type="showPassword ? 'text' : 'password'" 
              placeholder="请输入密码"
              prefix-icon="Lock"
            >
              <template #prefix>
                <el-icon><Lock /></el-icon>
              </template>
              <template #suffix>
                <el-icon @click="togglePasswordVisibility" style="cursor: pointer;">
                  <Eye v-if="showPassword" />
                  <EyeOff v-else />
                </el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item>
            <el-checkbox v-model="rememberMe" class="remember-me">记住我</el-checkbox>
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              @click="handleLogin" 
              :loading="loading" 
              class="login-button w-full"
            >
              登录
            </el-button>
          </el-form-item>
        </el-form>
        <div class="login-footer">
          <a href="#" class="footer-link">忘记密码？</a>
          <a href="#" class="footer-link ml-4">立即注册</a>
        </div>
      </div>
      <div class="login-sidebar">
        <div class="sidebar-content">
          <h2>量化交易</h2>
          <p>用数据驱动决策，让算法管理投资</p>
          <ul class="feature-list">
            <li>
              <span class="feature-icon">📊</span>
              <span>多策略回测</span>
            </li>
            <li>
              <span class="feature-icon">⚡</span>
              <span>高性能计算</span>
            </li>
            <li>
              <span class="feature-icon">🔧</span>
              <span>自定义策略</span>
            </li>
            <li>
              <span class="feature-icon">📈</span>
              <span>实时监控</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.login-wrapper {
  display: flex;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  width: 900px;
  max-width: 90%;
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-form {
  flex: 1;
  padding: 40px;
  display: flex;
  flex-direction: column;
}

.login-sidebar {
  flex: 1;
  background: linear-gradient(135deg, #409EFF 0%, #67C23A 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: #303133;
  margin: 0 0 8px 0;
}

.login-subtitle {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

.form-container {
  margin-bottom: 20px;
}

.login-button {
  font-size: 16px;
  padding: 12px 0;
  border-radius: 8px;
  background: linear-gradient(135deg, #409EFF 0%, #67C23A 100%);
  border: none;
  transition: all 0.3s ease;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.login-button:disabled {
  transform: none;
  box-shadow: none;
}

.remember-me {
  color: #606266;
  font-size: 14px;
}

.login-footer {
  display: flex;
  justify-content: center;
  margin-top: auto;
  padding-top: 20px;
}

.footer-link {
  color: #409EFF;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.3s ease;
}

.footer-link:hover {
  color: #66b1ff;
}

.ml-4 {
  margin-left: 16px;
}

.sidebar-content {
  text-align: center;
}

.sidebar-content h2 {
  font-size: 32px;
  margin-bottom: 16px;
  font-weight: 700;
}

.sidebar-content p {
  font-size: 16px;
  margin-bottom: 32px;
  opacity: 0.9;
}

.feature-list {
  list-style: none;
  padding: 0;
}

.feature-list li {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  font-size: 18px;
  opacity: 0.9;
  transition: opacity 0.3s ease;
}

.feature-list li:hover {
  opacity: 1;
}

.feature-icon {
  font-size: 24px;
  margin-right: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-wrapper {
    flex-direction: column;
    max-width: 400px;
  }
  
  .login-sidebar {
    display: none;
  }
  
  .login-form {
    padding: 30px 20px;
  }
}
</style>