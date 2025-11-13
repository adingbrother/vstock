# 架构与技术选型（QuantWeb）

此文档概述项目的“为什么”和“怎么做”，供开发者与自动化编码代理参考。它是从项目需求文档（量化投研 Web 平台 Prompt）精炼出的实现决策、组件边界、数据流与运行/部署注意事项。

1) 总体架构（高层）
- 浏览器（Vue3 + Vite） ↔ FastAPI 网关（REST + WebSocket） ↔ 业务服务（异步 Service + Celery 任务） ↔ 数据层（SQLAlchemy + SQLite 默认 / MySQL 可选） ↔ 存储（本地文件/HDF5；S3 预留）
- Redis 作为缓存与 Celery broker；Celery worker 负责耗时任务（下载、回测、推荐、报告生成）。

2) 关键技术栈（已确认默认值）
- Python: 3.11.7
- Web 框架: FastAPI 0.110 + uvicorn
- 异步任务: Celery 5.x + Redis 7
- ORM: SQLAlchemy 2.x
- 数据源: AkShare / Tushare（网络 SDK）
- 前端: Vue3 + TypeScript + Vite + Element-Plus + Monaco Editor
- 容器: Docker + docker-compose

3) 主要目录与职责（代码示例参考）
- `quant_web/main.py`：应用入口，包含路由注册与 WebSocket `/ws/{task_id}`。确保 uvicorn 启动参数与 workers 配置一致。
- `quant_web/api/v1/`：REST 路由实现（data.py, backtest.py, strategy.py, recommend.py）。所有接口应返回明确错误码（参考文档示例 `40001`）。
- `quant_web/core/`：核心服务实现（dm/akshare_adapter.py、be/matcher.py、re/factor_model.py 等）。常量集中在 `core/const.py`。
- `models/`：SQLAlchemy model 与 DB 会话管理（database.py）。
- `scripts/`：运维与 CI 脚本（backup.sh、health_check.sh、migrate.sh）。

4) 数据流与关键交互
- 下载流程：前端 → POST /api/v1/data/download → 后端入队 Celery 任务 → akshare/tushare 拉取 → 数据清洗 → 写入 DB/Kline 表 → WebSocket 推送进度。
- 回测流程：前端 → POST /api/v1/backtest/submit → 任务写入 DB 状态 Pending → Celery worker 执行回测引擎（matcher、撮合逻辑）→ 结果写入 report + DB → 前端通过 WS/REST 拉取报告。
- 推荐流程：定期/即时触发因子评分模块，使用 `FACTOR_WEIGHTS` 计算得分并写入 `recommend_result` 表。

5) 非功能注意事项
- 依赖安装：Dockerfile 中应包含必要系统库（建议：libgomp1, libhdf5-serial-dev, build-essential），以减少 numpy/akshare 安装问题。
- 策略沙箱：必须实现 AST 白名单 + 子进程执行 + `resource.setrlimit` 限制 CPU/内存（默认 30 分钟、2GB）。禁止 `os/sys/subprocess` 等敏感模块。
- 日志与监控：使用 JSON 日志格式，提供 /api/health 接口；建议采集 Prometheus 指标（backtest_duration_seconds 等）。

6) 部署与运行（常用命令）
```bash
# 后端本地开发
python3 -m uvicorn quant_web.main:app --host 0.0.0.0 --port 8000 --reload

# 使用 docker-compose（包含 redis、worker）
docker-compose up --build

# 运行测试
pytest -q
```

7) 扩展与性能规划
- 初始目标以 SQLite 为主（本地单用户）。当股票数或 K 线量增大时，可迁移到 MySQL（使用分区表）并启用读写分离。
- 回测并行度通过 Celery worker 数量调节，任务超时/内存门禁通过配置常量控制。

8) 决策记录（已确认）
- Python=3.11.7；Node=18.19.0；默认 DB=SQLite；在 Dockerfile 安装系统依赖；沙箱白名单见 CONFIRM.md（默认：numpy,pandas,talib,math,statistics）。

---
后续：在你确认这些默认值后（已确认），我将开始生成项目基础骨架（`quant_web/`、`frontend/`、Dockerfile、docker-compose.yml、requirements.txt、package.json、scripts/`），并添加基础可运行示例接口与测试。 
