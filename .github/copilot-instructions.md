# .github/copilot-instructions.md — 项目专用 AI 代理说明

目标：让 AI 代码代理快速产出可运行、与项目约定一致的代码，避免常见破坏性更改。

要点（简短清单）
- 项目主要目录：`quant_web/`（后端）、`frontend/`（前端）、`sql/`、`scripts/`、`tests/`、`docs/`。
- 所有魔法值/常量必须引用 `quant_web/core/const.py`，不要直接硬编码数值、路径或错误码。
- REST 路由在 `quant_web/api/v1/`；任何新增接口必须同时添加对应测试到 `tests/` 并更新 Swagger（FastAPI 自动导出）。
- 外部 SDK 调用（AkShare/Tushare）必须含重试、指数退避和日志（参见 `docs/architecture.md`）。
- 策略沙箱：实现 AST 白名单 + 子进程执行 + `resource.setrlimit`，禁止敏感模块（`os`, `sys`, `subprocess`）。

快速可运行目标（何为“通过”）
- `docker-compose up --build` 能启动 `web`、`redis`、`worker` 三个服务；访问 `http://localhost:8000/docs` 可见 API 文档。
- `POST /api/v1/data/download` 返回 `202` 且包含 `task_id`；WebSocket `/ws/{task_id}` 能接受消息（可用模拟消息）。

示例片段（实现约定）
- 下载函数应遵循：
  - 使用 `MAX_RETRY` 重试；指数退避 `sleep = base * 2**attempt + random.uniform(0,1)`；日志使用 `loguru`。
  - 返回 DataFrame 且列名规范化为 `[trade_date, open, high, low, close, vol, amount]`。

代码生成约束（严格）
- 不允许生成带 `TODO` 或占位符的文件。必须实现分支与异常处理。
- 数据库迁移脚本必须幂等（使用 `INSERT OR IGNORE` 或先检查存在性）。
- 所有新增依赖须写入 `requirements.txt`（后端）或 `frontend/package.json`（前端），并在 CI 中被安装。

审阅指引（AI 生成后人类复核要点）
- 检查是否直接硬编码魔法值（若有，拒绝合并）；检查是否使用 `core/const.py`。
- 核对外部网络调用是否有超时/重试与单元测试 Mock。若无，要求添加。 

参考文件（阅读这些文件能迅速理解项目约定）
- `docs/architecture.md`（架构/运行/决策）
- `quant_web/core/const.py`（常量）
- `quant_web/api/v1/`（接口）
- `tests/`（测试约定）

如需修改此指南，请在 PR 描述里说明为什么要放宽或收紧某条约束，并列出受影响的文件。
