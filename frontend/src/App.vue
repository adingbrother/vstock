<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <el-header height="60px" class="app-header">
      <div class="header-content">
        <div class="logo-title">
          <el-icon class="logo-icon"><TrendCharts /></el-icon>
          <h1>量化投研平台</h1>
        </div>
        <div class="header-info">
          <el-dropdown>
            <span class="user-info">
              <el-avatar size="small" icon="User" />
              <span>管理员</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>个人中心</el-dropdown-item>
                <el-dropdown-item>系统设置</el-dropdown-item>
                <el-dropdown-item divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </el-header>

    <div class="app-main-layout">
      <!-- 侧边导航栏 -->
      <el-aside width="240px" class="app-sidebar">
        <el-menu
          :default-active="activeMenu"
          class="sidebar-menu"
          router
          :collapse-transition="true"
          background-color="#001529"
          text-color="#fff"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/">
            <el-icon><PieChart /></el-icon>
            <template #title>数据仪表盘</template>
          </el-menu-item>
          <el-menu-item index="/backtest">
            <el-icon><LineChart /></el-icon>
            <template #title>策略回测</template>
          </el-menu-item>
          <el-menu-item index="/strategy">
            <el-icon><MagicStick /></el-icon>
            <template #title>策略管理</template>
          </el-menu-item>
          <el-menu-item index="/data">
            <el-icon><Database /></el-icon>
            <template #title>数据管理</template>
          </el-menu-item>
          <el-menu-item index="/tasks">
            <el-icon><List /></el-icon>
            <template #title>任务管理</template>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <template #title>系统设置</template>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区域 -->
      <el-main class="app-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </div>

    <!-- 底部信息 -->
    <el-footer height="40px" class="app-footer">
      <p>&copy; 2024 量化投研平台 | 服务器运行中</p>
    </el-footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { 
  TrendCharts, 
  PieChart, 
  LineChart, 
  MagicStick, 
  Database, 
  List, 
  Setting, 
  User, 
  ArrowDown 
} from '@element-plus/icons-vue'

// 获取当前路由
const route = useRoute()

// 计算当前激活的菜单
const activeMenu = computed(() => {
  return route.path || '/'
})

// 页面加载时的初始化
onMounted(() => {
  // 可以在这里添加一些全局初始化逻辑
  console.log('量化投研平台已加载')
})
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
  overflow: hidden;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f0f2f5;
}

#app {
  height: 100vh;
  overflow: hidden;
}

.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部导航栏样式 */
.app-header {
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.header-content {
  height: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
}

.logo-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  font-size: 28px;
  color: #409EFF;
}

.logo-title h1 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #303133;
}

.header-info {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 4px;
  transition: all 0.3s;
}

.user-info:hover {
  background-color: #f5f7fa;
}

.user-info span {
  font-size: 14px;
  color: #606266;
}

/* 主布局样式 */
.app-main-layout {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 侧边栏样式 */
.app-sidebar {
  background-color: #001529;
  overflow-y: auto;
}

.sidebar-menu {
  height: 100%;
  border-right: none;
}

.sidebar-menu .el-menu-item {
  height: 60px;
  line-height: 60px;
  font-size: 14px;
  transition: all 0.3s;
}

.sidebar-menu .el-menu-item:hover {
  background-color: #1890ff !important;
}

.sidebar-menu .el-menu-item.is-active {
  background-color: #1890ff !important;
  border-right: 4px solid #409EFF;
}

.sidebar-menu .el-icon {
  font-size: 18px;
  margin-right: 10px;
}

/* 主内容区域样式 */
.app-content {
  padding: 24px;
  background-color: #f0f2f5;
  overflow-y: auto;
}

/* 底部样式 */
.app-footer {
  background: white;
  border-top: 1px solid #ebeef5;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-footer p {
  margin: 0;
  font-size: 13px;
  color: #909399;
}

/* 页面过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .app-sidebar {
    width: 200px !important;
  }
  
  .logo-title h1 {
    font-size: 18px;
  }
  
  .app-content {
    padding: 16px;
  }
}

@media (max-width: 768px) {
  .app-sidebar {
    position: fixed;
    left: -240px;
    top: 60px;
    bottom: 40px;
    transition: left 0.3s;
    z-index: 999;
  }
  
  .app-sidebar.show {
    left: 0;
  }
  
  .header-content {
    padding: 0 16px;
  }
  
  .logo-title h1 {
    font-size: 16px;
  }
  
  .user-info span {
    display: none;
  }
}
</style>
