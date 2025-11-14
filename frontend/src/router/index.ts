import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'

// 路由配置
const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { title: '量化投研平台' }
  },
  {
    path: '/backtest',
    name: 'Backtest',
    component: () => import('../views/Backtest.vue'),
    meta: { title: '策略回测' }
  },
  {
    path: '/data',
    name: 'Data',
    component: () => import('../views/Data.vue'),
    meta: { title: '数据管理' }
  },
  {
    path: '/tasks',
    name: 'Tasks',
    component: () => import('../views/Tasks.vue'),
    meta: { title: '任务管理' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue'),
    meta: { title: '系统设置' }
  },
  {
    path: '/gitservice',
    name: 'GitService',
    component: () => import('../views/GitMcpView.vue'),
    meta: { title: 'Git MCP服务演示' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/' // 404重定向到首页
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局前置守卫，设置页面标题
router.beforeEach((to, from, next) => {
  document.title = to.meta.title as string || '量化投研平台'
  next()
})

export default router
