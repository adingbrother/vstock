<template>
  <div class="git-mcp-demo">
    <h2>Git MCP服务使用示例</h2>
    
    <el-card class="git-operation-card">
      <template #header>
        <div class="card-header">
          <span>Git 操作</span>
        </div>
      </template>

      <el-tabs v-model="activeTab">
        <!-- 克隆仓库 -->
        <el-tab-pane label="克隆仓库" name="clone">
          <el-form :model="cloneForm" label-width="100px">
            <el-form-item label="仓库地址">
              <el-input v-model="cloneForm.repoUrl" placeholder="git://localhost/your-repo.git"></el-input>
            </el-form-item>
            <el-form-item label="本地路径">
              <el-input v-model="cloneForm.localPath" placeholder="./your-repo"></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleClone" :loading="loading">克隆</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 仓库状态 -->
        <el-tab-pane label="查看状态" name="status">
          <el-form :model="statusForm" label-width="100px">
            <el-form-item label="仓库路径">
              <el-input v-model="statusForm.localPath" placeholder="./your-repo"></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleStatus" :loading="loading">查看状态</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 拉取代码 -->
        <el-tab-pane label="拉取代码" name="pull">
          <el-form :model="pullForm" label-width="100px">
            <el-form-item label="仓库路径">
              <el-input v-model="pullForm.localPath" placeholder="./your-repo"></el-input>
            </el-form-item>
            <el-form-item label="分支">
              <el-input v-model="pullForm.branch" placeholder="main"></el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handlePull" :loading="loading">拉取</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 输出结果 -->
    <el-card v-if="outputVisible" class="result-card">
      <template #header>
        <div class="card-header">
          <span>执行结果</span>
          <el-button type="text" @click="clearOutput">清空</el-button>
        </div>
      </template>
      <el-alert
        :title="result.success ? '成功' : '失败'"
        :type="result.success ? 'success' : 'error'"
        :description="result.success ? result.output : result.error"
        show-icon
        :closable="false"
      ></el-alert>
      <pre v-if="result.output" class="output-content">{{ result.output }}</pre>
    </el-card>

    <!-- 关于MCP服务的说明 -->
    <el-card class="info-card">
      <template #header>
        <div class="card-header">
          <span>MCP服务说明</span>
        </div>
      </template>
      <div class="info-content">
        <p>1. 本示例通过前端应用访问配置在 <code>vite.config.ts</code> 中的git MCP服务</p>
        <p>2. MCP服务配置位于 <code>server.mcpServers['git-service']</code> 部分</p>
        <p>3. 服务使用git daemon运行在项目根目录，提供只读访问</p>
        <p>4. 可通过<code>git://localhost/</code>协议访问项目仓库</p>
        <p>5. 要启用写入权限，需要修改git daemon参数，添加<code>--enable=receive-pack</code></p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { GitMcpService } from '@/utils/gitMcpService';

// 状态管理
const activeTab = ref('clone');
const loading = ref(false);
const outputVisible = ref(false);
const result = reactive({
  success: false,
  output: '',
  error: ''
});

// 表单数据
const cloneForm = reactive({
  repoUrl: 'git://localhost/',
  localPath: './cloned-repo'
});

const statusForm = reactive({
  localPath: './cloned-repo'
});

const pullForm = reactive({
  localPath: './cloned-repo',
  branch: 'main'
});

// 处理克隆操作
async function handleClone() {
  loading.value = true;
  try {
    const res = await GitMcpService.clone(cloneForm.repoUrl, cloneForm.localPath);
    updateResult(res);
  } catch (error) {
    updateResult({
      success: false,
      output: '',
      error: error instanceof Error ? error.message : '克隆失败'
    });
  } finally {
    loading.value = false;
  }
}

// 处理状态查询
async function handleStatus() {
  loading.value = true;
  try {
    const res = await GitMcpService.status(statusForm.localPath);
    updateResult(res);
  } catch (error) {
    updateResult({
      success: false,
      output: '',
      error: error instanceof Error ? error.message : '获取状态失败'
    });
  } finally {
    loading.value = false;
  }
}

// 处理拉取操作
async function handlePull() {
  loading.value = true;
  try {
    const res = await GitMcpService.pull(pullForm.localPath, pullForm.branch);
    updateResult(res);
  } catch (error) {
    updateResult({
      success: false,
      output: '',
      error: error instanceof Error ? error.message : '拉取失败'
    });
  } finally {
    loading.value = false;
  }
}

// 更新结果显示
function updateResult(res: { success: boolean; output: string; error?: string }) {
  result.success = res.success;
  result.output = res.output;
  result.error = res.error || '';
  outputVisible.value = true;
}

// 清空输出
function clearOutput() {
  outputVisible.value = false;
  result.success = false;
  result.output = '';
  result.error = '';
}
</script>

<style scoped>
.git-mcp-demo {
  padding: 20px;
}

.git-operation-card,
.result-card,
.info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.output-content {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 10px;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  margin-top: 10px;
}

.info-content {
  line-height: 1.8;
}

.info-content code {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
}
</style>
