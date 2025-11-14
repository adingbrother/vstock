<template>
  <div class="git-mcp-view">
    <el-page-header
      :content="'Git MCP服务演示'"
      @back="handleBack"
    ></el-page-header>
    
    <div class="view-content">
      <GitMcpDemo />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import GitMcpDemo from '@/components/GitMcpDemo.vue';

const router = useRouter();

// 返回上一页
function handleBack() {
  router.back();
}
</script>

<style scoped>
.git-mcp-view {
  height: 100%;
  padding: 20px;
  background-color: #f0f2f5;
}

.view-content {
  background-color: #fff;
  border-radius: 6px;
  padding: 20px;
  margin-top: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
</style>
