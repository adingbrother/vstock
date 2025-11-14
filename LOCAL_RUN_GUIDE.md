# 量化投研平台本地运行指南

## 系统概述

这是一个个人量化投研 Web 平台，用于策略开发、回测和管理。系统采用前后端分离架构：
- 前端：Vue 3 + Element Plus
- 后端：Python FastAPI

## 环境要求

### 必备软件

1. **Python 3.8+**
   - 检查版本：`python3 --version`
   - 安装：从 [Python官网](https://www.python.org/downloads/) 下载

2. **Node.js 16+ 和 npm**
   - 检查版本：`node --version` 和 `npm --version`
   - 安装：从 [Node.js官网](https://nodejs.org/) 下载

## 后端服务安装与运行

### 1. 安装Python依赖

```bash
# 进入项目根目录
cd /Users/wangxx/Desktop/python3/vstock

# 创建虚拟环境（推荐）
python3 -m venv .venv

# 激活虚拟环境
source .venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

### 2. 初始化数据库（可选）

```bash
# 运行数据库初始化脚本
python3 scripts/init_db.py
```

### 3. 启动后端服务

```bash
# 使用uvicorn启动后端服务
python3 -m uvicorn quant_web.main:app --host 0.0.0.0 --port 8000 --reload
```

服务成功启动后，你可以访问：
- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/api/v1/health

## 前端服务安装与运行

### 1. 安装Node.js依赖

```bash
# 进入前端目录
cd /Users/wangxx/Desktop/python3/vstock/frontend

# 安装依赖
npm install
```

### 2. 启动前端开发服务器

```bash
# 启动开发服务器
npm run dev
```

服务成功启动后，你可以访问：
- 前端应用：http://localhost:5173/

## 系统功能使用说明

### 访问系统

打开浏览器，访问 http://localhost:5173/ 进入量化投研平台。

### 主要功能模块

通过左侧导航栏可以访问以下功能：

1. **数据仪表盘**
   - 查看系统概览和关键指标
   - 监控策略运行状态和收益率
   - 查看系统告警信息

2. **策略回测**
   - 创建和运行策略回测
   - 设置回测参数
   - 查看回测结果和性能分析

3. **策略管理**
   - 创建、编辑和删除策略
   - 管理策略参数和配置

4. **数据管理**
   - 导入和管理金融数据
   - 设置数据更新规则

5. **任务管理**
   - 查看任务队列和执行状态
   - 管理后台任务

6. **系统设置**
   - 配置系统参数
   - 管理用户设置

7. **Git MCP服务**
   - 执行Git操作（克隆、拉取等）
   - 管理代码仓库

### 常用操作流程

#### 1. 创建并运行策略回测

1. 点击左侧导航栏的「策略回测」
2. 填写策略名称和代码
3. 设置回测时间范围和初始资金
4. 点击「运行回测」按钮
5. 在任务管理页面查看回测进度
6. 回测完成后，查看详细的回测报告

#### 2. 导入数据

1. 点击左侧导航栏的「数据管理」
2. 点击「导入数据」按钮
3. 选择数据文件或输入数据来源
4. 设置数据导入参数
5. 确认导入

## 常见问题与解决方案

### 1. 依赖安装失败

**问题**：pip install 或 npm install 失败

**解决方案**：
- 确保网络连接正常
- 对于pip失败：检查Python版本，尝试使用 `pip install --default-timeout=100 package_name`
- 对于npm失败：尝试使用 `npm install --registry=https://registry.npmmirror.com`

### 2. 端口冲突

**问题**：启动服务时提示端口已被占用

**解决方案**：
- 关闭占用端口的进程
- 或修改服务启动端口：
  - 后端：`python3 -m uvicorn quant_web.main:app --port 8001`
  - 前端：修改 vite.config.ts 中的端口配置

### 3. 数据库连接错误

**问题**：无法连接到数据库

**解决方案**：
- 确保数据库文件存在于正确位置
- 运行数据库初始化脚本：`python3 scripts/init_db.py`

### 4. 前端无法连接到后端

**问题**：前端页面加载但无法获取数据

**解决方案**：
- 确保后端服务正在运行
- 检查前端配置中的API地址是否正确
- 查看浏览器控制台的错误信息

## 开发提示

1. **热重载**
   - 后端使用 `--reload` 参数可以在代码修改后自动重启
   - 前端开发服务器也支持热重载

2. **调试**
   - 后端API文档提供了交互式调试界面：http://localhost:8000/docs
   - 前端可以使用浏览器开发者工具进行调试

3. **日志**
   - 后端日志直接输出到控制台
   - 系统日志保存在 `logs/` 目录下

## 注意事项

1. 本系统目前是骨架实现，部分功能可能尚未完全实现
2. 建议定期备份策略和数据文件
3. 在生产环境中部署时，请配置适当的安全措施
4. 对于大数据量的处理，可能需要增加系统资源配置

---

祝您使用愉快！如有任何问题，请参考代码注释或API文档。