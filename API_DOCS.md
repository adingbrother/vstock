# QuantWeb API 文档

本文档提供了 QuantWeb 量化交易平台的 API 使用指南。

## 访问自动生成的文档

QuantWeb 使用 FastAPI 框架，自动生成了交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

这些文档支持在线测试所有 API 端点，包括请求参数验证和响应格式展示。

## API 版本

当前版本: v0.0.1

## 基础 URL

所有 API 端点的基础 URL 为: `http://localhost:8000/api/v1`

## API 模块

### 1. 数据管理 (data)

提供股票数据的下载、查询和管理功能。

**主要端点**:

- `POST /api/v1/data/download`: 下载股票数据
- `GET /api/v1/data/tasks/{task_id}`: 获取下载任务状态
- `GET /api/v1/data/sources`: 获取支持的数据源列表
- `GET /api/v1/data/stocks`: 获取已下载的股票列表
- `POST /api/v1/data/query`: 查询股票数据
- `DELETE /api/v1/data/stocks/{stock_code}`: 删除指定股票数据
- `GET /api/v1/data/cache/info`: 获取缓存信息
- `POST /api/v1/data/cache/clear`: 清空缓存

### 2. 策略管理 (strategy)

提供量化交易策略的创建、配置和管理功能。

**主要端点**:

- `GET /api/v1/strategy/list`: 获取策略列表
- `GET /api/v1/strategy/info`: 获取策略信息
- `POST /api/v1/strategy/create`: 创建策略实例
- `GET /api/v1/strategy/get`: 获取策略实例
- `PUT /api/v1/strategy/update`: 更新策略实例
- `DELETE /api/v1/strategy/delete`: 删除策略实例
- `GET /api/v1/strategy/instances`: 列出所有策略实例

### 3. 回测引擎 (backtest)

提供策略回测功能，用于评估交易策略的历史表现。

**主要端点**:

- `POST /api/v1/backtest`: 提交回测任务
- `GET /api/v1/backtest/{task_id}`: 获取回测任务状态
- `GET /api/v1/backtest/{task_id}/result`: 获取回测结果

### 4. 推荐引擎 (recommend)

提供股票推荐和因子分析功能。

**主要端点**:

- `POST /api/v1/recommend`: 创建推荐任务
- `GET /api/v1/recommend/{task_id}`: 获取推荐任务状态
- `GET /api/v1/recommend/{task_id}/result`: 获取推荐结果
- `GET /api/v1/recommend/factors`: 获取因子配置
- `PUT /api/v1/recommend/factors`: 更新因子配置
- `GET /api/v1/recommend/history`: 获取推荐历史

## WebSocket 接口

QuantWeb 提供 WebSocket 接口用于实时任务状态更新：

- `ws://localhost:8000/ws/tasks`: 批量任务管理
- `ws://localhost:8000/ws/{task_id}`: 单任务更新

## 健康检查

- `GET /api/v1/health`: 检查服务健康状态

## 错误处理

所有 API 错误响应都遵循统一格式，包含错误代码和详细描述。常见错误码如下：

- `40401`: 任务不存在
- `50001`: 创建任务失败

## 认证

当前版本暂未实现认证功能。后续版本将添加JWT认证机制。

## 联系我们

如有任何问题或建议，请联系开发团队。