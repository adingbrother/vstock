 个人量化投研 Web 平台  

 大模型可直接开发版需求规格 + 详细设计文档  

版本：v5.0-Final（冲突已合并，开发级细化）  

更新：2024-01-26  

目的：给大模型研发人员一次性生成全部代码，零歧义，零人工补充  

 1. 文档使用说明（给大模型的 Prompt）

你是一名「全栈量化平台架构师」，请依据以下结构化需求+设计+原型+测试+运维内容，一次性生成可直接运行的 Python/FastAPI + Vue3 + SQL + Docker完整工程。  

禁止遗漏：函数原型、字段约束、分支异常、测试用例、运维脚本、上线检查单。  

禁止歧义：所有常量、魔法值、路径、命名、索引、错误码均已明确。  

 2. 项目元信息（不变）

| 字段 | 值 |

|||

| 产品名 | 个人量化投研 Web 平台 |

| 版本 | v5.0-Final |

| 交付 | 本地 Web 服务器 + 浏览器 |

| 目标 | 个人量化爱好者、高校、小私募 |

| 边界 | 仅投研，无实盘；单用户；本地部署；4C8G 流畅 |

 3. 总体架构（冲突已合并）

浏览器层：Vue3 + TS + Element-Plus + ECharts5 + Monaco

网关层：FastAPI 0.110 + uvicorn 4 workers + CORS全开

业务层：异步Service + Celery 5.3 + Redis 7

数据层：SQLAlchemy 2.0 + SQLite默认+MySQL可选+分区表

存储层：本地文件 + HDF5 + ./data/ + ./backup/ + S3预留

 4. 业务泳道（不变）

见 mermaid 序列图（第2章）  

 5. 功能模块树（冲突已合并）

├─ DM 数据管理

│  ├─ DM-01 多源接入（AkShare/Tushare适配器）

│  ├─ DM-02 数据清洗（缺失、异常、复权）

│  ├─ DM-03 存储与版本（SQLite+分区+备份）

│  └─ DM-04 查询API（REST+Redis缓存）

├─ SM 策略管理

│  ├─ SM-01 Monaco编辑器（补全、语法、主题）

│  ├─ SM-02 模板市场（12策略）

│  ├─ SM-03 参数可视化（g_params表单）

│  └─ SM-04 导入导出（.py/.zip+加密可选）

├─ BE 回测引擎

│  ├─ BE-01 任务生命周期（Pending→Success）

│  ├─ BE-02 撮合子引擎（限价/市价/滑点/手续费）

│  ├─ BE-03 绩效指标（收益、风险、交易统计）

│  └─ BE-04 异常熔断（超时、内存、代码异常）

├─ RE 推荐引擎

│  ├─ RE-01 推荐策略管理（单策略vs融合权重）

│  ├─ RE-02 多因子评分（收益40%稳定30%活跃20%质量10%）

│  ├─ RE-03 Top-N列表（强烈/关注/谨慎三档）

│  └─ RE-04 效果追踪（5/10/20日胜率、用户反馈）

├─ VIS 可视化

│  ├─ VIS-01 K线+指标+信号（ECharts交互）

│  ├─ VIS-02 资金曲线（权益+回撤+基准）

│  ├─ VIS-03 推荐雷达图（五维因子）

│  └─ VIS-04 热力图（股票×策略评分矩阵）

└─ SYS 系统管理

   ├─ SYS-01 系统配置（数据源、缓存、性能阈值）

   ├─ SYS-02 健康监控（CPU/内存/磁盘/队列）

   └─ SYS-03 日志与告警（分级、轮转、邮件可选）

 6. 详细设计（函数级原型 + 分支 + 异常 + 常量）

 6.1 常量与魔法值（全局禁止硬编码）

python

 quant_web/core/const.py

```python
AK_SLEEP = 0.5           AkShare 请求间隔（秒）
```

```python
MAX_RETRY = 3            下载重试次数
```

```python
SLIP_RANGE = (-0.01, 0.01)   滑点随机范围（元）
```

```python
MAX_DD_THRESHOLD = 0.2   最大回撤告警阈值（20%）
```

```python
WORKER_MAX_MEM = 2_000_000_000   2GB 内存熔断（字节）
```

```python
BATCH_SIZE = 1000        数据库 bulk_insert 批大小
```

```python
QUALITY_SCORE_MIN = 60   数据质量最低分
```

```python
FACTOR_WEIGHTS = {
```

```python
"return": 0.4,
```

```python
"stability": 0.3,
```

```python
"active": 0.2,
```

```python
"quality": 0.1
```

}

 6.2 函数级原型（伪代码→可直接实现）

 DM-01-01 下载函数（含分支+异常）

python

 quant_web/core/dm/akshare_adapter.py

```python
import akshare as ak
```

```python
import pandas as pd
```

```python
import asyncio
```

```python
from loguru import logger
```

```python
from const import AK_SLEEP, MAX_RETRY, BATCH_SIZE
```

```python
class AkShareAdapter:
```

```python
async def download_daily(self, ts_code: str, start: str, end: str) -> pd.DataFrame:
```

```python
"""下载日线；返回标准 DF [trade_date, open, high, low, close, vol, amount]"""
```

```python
for attempt in range(1, MAX_RETRY + 1):
```

```python
try:
```

```python
code = self._to_ak_code(ts_code)
```

```python
df = await asyncio.to_thread(ak.stock_zh_a_hist, symbol=code, period="daily", start_date=start, end_date=end)
```

```python
if df is None or df.empty:
```

```python
raise ValueError(f"AkShare 返回空数据 {ts_code} 尝试={attempt}")
```

```python
df = df.rename(columns={
```

```python
"日期": "trade_date", "开盘": "open", "收盘": "close", "最高": "high", "最低": "low", "成交量": "vol", "成交额": "amount"
```

```python
})
```

```python
df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y%m%d")
```

```python
df["source"] = "akshare"
```

```python
await asyncio.sleep(AK_SLEEP)
```

```python
logger.info(f"AkShare 下载完成 {ts_code} {len(df)} 条")
```

```python
return df
```

```python
except Exception as e:
```

```python
logger.warning(f"AkShare 下载失败 {ts_code} 尝试={attempt} {e}")
```

```python
if attempt == MAX_RETRY:
```

```python
raise e
```

```python
await asyncio.sleep(attempt  2)   指数退避
```

 BE-02-01 撮合函数（分支+滑点常量）

python

 quant_web/core/be/matcher.py

```python
import random
```

```python
from const import SLIP_RANGE
```

```python
from models.trade import Order, Trade, Bar
```

```python
class SimpleMatcher:
```

```python
def match(self, order: Order, bar: Bar) -> Optional[Trade]:
```

```python
"""返回 Trade 或 None；常量滑点"""
```

```python
if order.order_type == "market":
```

```python
price = bar.close + random.uniform(SLIP_RANGE)
```

```python
return Trade(ts_code=order.ts_code, price=round(price, 2), qty=order.qty, side=order.side)
```

```python
if order.order_type == "limit":
```

```python
if (order.side == "buy" and bar.low <= order.price) or (order.side == "sell" and bar.high >= order.price):
```

```python
return Trade(ts_code=order.ts_code, price=order.price, qty=order.qty, side=order.side)
```

```python
return None
```

 RE-02-01 多因子评分（权重常量+公式）

python

 quant_web/core/re/factor_model.py

```python
from const import FACTOR_WEIGHTS
```

```python
class FactorModel:
```

```python
def score(self, stock: str, results: list[StrategyResult]) -> float:
```

```python
"""返回 0-100 综合分；权重见常量"""
```

```python
raw = {f: self._calc(f, stock, results) for f in FACTOR_WEIGHTS}
```

```python
z_score = {k: (v - self.stats[k]['mean']) / self.stats[k]['std'] for k, v in raw.items()}
```

```python
weighted = sum(z_score[f]  FACTOR_WEIGHTS[f] for f in FACTOR_WEIGHTS)
```

```python
return 50 + 10  weighted   映射到 0-100
```

 7. 数据库设计（字段级+约束+索引+分区DDL）

 7.1 股票列表

sql

- - SQLite

```python
CREATE TABLE stock_basic (
```

```python
ts_code TEXT PRIMARY KEY,          -- 000001.SZ
```

```python
symbol TEXT NOT NULL,              -- 000001
```

```python
name TEXT NOT NULL,                -- 平安银行
```

```python
area TEXT,                         -- 深圳
```

```python
industry TEXT,                     -- 银行
```

```python
list_date TEXT,                    -- 19910403
```

```python
data_source TEXT DEFAULT 'akshare' CHECK(data_source IN ('akshare','tushare')),
```

```python
status INTEGER DEFAULT 1 CHECK(status IN (0,1)),
```

```python
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

);

```python
CREATE INDEX idx_sb_industry ON stock_basic(industry);
```

 7.2 K 线分区表（MySQL 语法）

sql

```python
CREATE TABLE kline_000001_sz (
```

```python
trade_date DATE NOT NULL,
```

```python
open DECIMAL(10,2) NOT NULL CHECK(open >= 0),
```

```python
high DECIMAL(10,2) NOT NULL CHECK(high >= 0),
```

```python
low DECIMAL(10,2) NOT NULL CHECK(low >= 0),
```

```python
close DECIMAL(10,2) NOT NULL CHECK(close >= 0),
```

```python
vol BIGINT NOT NULL CHECK(vol >= 0),
```

```python
amount DECIMAL(20,2) NOT NULL CHECK(amount >= 0),
```

```python
source TEXT CHECK(source IN ('akshare','tushare')),
```

```python
PRIMARY KEY (trade_date)
```

```python
) PARTITION BY RANGE (YEAR(trade_date)) (
```

```python
PARTITION p2020 VALUES LESS THAN (2021),
```

```python
PARTITION p2021 VALUES LESS THAN (2022),
```

```python
PARTITION p2022 VALUES LESS THAN (2023),
```

```python
PARTITION p2023 VALUES LESS THAN (2024),
```

```python
PARTITION p2024 VALUES LESS THAN (2025)
```

);

 8. 接口规范（字段级+示例+错误码）

 8.1 下载提交

POST /api/v1/data/download

Request:

{

  "stock_list": ["000001.SZ", "600000.SH"],

  "start_date": "20230101",

  "end_date": "20231231",

  "source": "akshare"

}

Response 202:

{

  "task_id": "DL_1700000001",

  "status": "Pending",

  "estimated_seconds": 120

}

WebSocket push:

{"type": "progress", "task_id": "DL_1700000001", "percent": 45, "message": "000001.SZ 已下载"}

Error 400:

{"code": 40001, "message": "start_date 格式错误"}

 8.2 回测提交

POST /api/v1/backtest/submit

Request:

{

  "strategy_id": "st_0001",

  "stock_pool": ["000001.SZ"],

  "start_date": "20230101",

  "end_date": "20231231",

  "init_cash": 100000,

  "params": {"fast": 5, "slow": 20}

}

Response 202:

{"task_id": "BK_1700000002", "status": "Pending"}

 9. 安全设计（OWASP Top10 对照+实现）

| 风险 | 具体实现 |

|||

| A01 访问控制 | 单用户默认 local_user；JWT 可选；文件权限 600 |

| A02 加密失败 | Token 字段 AES-256-CBC 加密；HTTPS 预留 |

```python
| A03 注入 | SQLAlchemy ORM；所有参数化查询；用户策略沙箱（禁止 import os/sys） |
```

| A04 不安全设计 | 策略超时 30min 强制 kill；内存上限 2GB；滑点/手续费常量不可修改 |

| A05 安全配置 | 生产环境关闭 /docs；CORS 白名单；Redis 无密码本地 |

| A06 组件漏洞 | pip-audit CI 阶段；requirements 锁定；bandit 扫描 |

| A09 日志记录 | 统一 log ID；错误堆栈不返前端；日志级别 INFO |

```python
| A10 SSRF | 下载域名白名单；策略内禁止 http 请求；限制 import |
```

 10. 性能与扩展性（数值+预留）

| 场景 | 当前目标 | 10× 预留方案 |

| 股票数 | 1 万 | MySQL 分区+读写分离 |

| K 线量 | 1 亿条 | 按年分区+HDF5+S3 |

| 并发回测 | 3 任务 | Celery Worker 横向 30 |

| 前端渲染 | 5k K 线点 | ECharts 采样 50k |

性能门禁：

- 单股票回测 1 年日线 ≤ 8s（4C8G）

- 下载 100 只股票日线 ≤ 120s

- WebSocket 推送延迟 ≤ 500ms

 11. 开发排期（人时级甘特图）

 11.1 人力池

- 后端：3 人（A/B/C）

- 前端：2 人（D/E）

- 测试：1 人（F）

```python
- 总计：6 人 × 8h × 5d × 8 周 = 1920 人时
```

 11.2 关键路径（人时）

| 任务 | 人时 | 依赖 | 开始 | 结束 |

||

| AkShare 适配器 | 32h | — | D1 | D2 |

| DAO+分区表 | 24h | AkShare | D2 | D3 |

| 撮合引擎 | 48h | DAO | D5 | D7 |

| 报告生成 | 32h | 撮合 | D9 | D10 |

| ECharts K 线 | 40h | 报告 | D13 | D15 |

| 集成测试 | 80h | K 线 | D15 | D20 |

```python
▣ 关键路径工时：32+24+48+32+40+80 = 256h（4.3 人周）
```

 11.3 甘特图（周）

周1：DM-01 完成（AkShare+DAO）

周2：DM-02 完成（清洗+质量）

周3：SM-01 完成（Monaco+模板）

周4：BE-01 完成（撮合+指标）

周5：BE-02 完成（报告+日志）

周6：RE-01 完成（因子+评分）

周7：VIS-01 完成（K 线+资金曲线）

周8：测试+文档+上线

 12. 测试策略（门禁→用例→自动化）

 12.1 质量门禁

- 单元测试覆盖率 ≥ 80%（pytest-cov）

- 核心接口 P95 延迟 ≤ 500ms（locust）

- 并发 3 回测任务无崩溃（stress）

- 内存峰值 ≤ 2GB/任务（memory_profiler）

 12.2 测试金字塔

| 层级 | 占比 | 工具 | 指标 |

|

| 单元 | 80% | pytest+cov | ≥ 80% 行覆盖 |

| 集成 | 15% | pytest-asyncio | 核心流程无报错 |

| E2E | 5% | Cypress | 主流程 < 2min |

 12.3 核心用例（小时级）

| ID | 描述 | 输入 | 预期 | 工时 |

||

| UT-DM-01 | 下载 000001.SZ 2023 | ts_code, start, end | DataFrame ≥ 240 行；无 NaN | 2h |

| IT-BE-01 | 双均线回测 | 000001.SZ, 2023 | 收益率与聚宽误差 < 0.1% | 4h |

| PT-PERF-01 | 10 用户并发回测 | locust 10 并发 | P95 ≤ 500ms；错误率 0% | 4h |

 12.4 自动化 CI/CD

yaml

 .github/workflows/ci.yml

name: ci

on: [push]

jobs:

  build:

```python
runs-on: ubuntu-latest
```

```python
steps:
```

```python
- uses: actions/checkout@v3
```

```python
- uses: actions/setup-python@v4
```

```python
with: {python-version: '3.11'}
```

```python
- run: pip install pip-audit pytest pytest-cov locust
```

```python
- run: pip-audit
```

```python
- run: pytest --cov=80 --cov-report=xml
```

```python
- run: locust -f tests/perf/locustfile.py --headless -u 10 -r 2 -t 30s --csv=perf
```

```python
- run: docker build -t quant-web .
```

 13. 交付与上线 Checklist（可勾选）

 13.1 代码交付

- [ ] main.py 一键启动验证（Win/Mac/Linux）

- [ ] requirements.txt 版本锁定 + pip-audit 通过

- [ ] Dockerfile + docker-compose.yml 构建成功

- [ ] alembic upgrade head 无报错

 13.2 文档交付

- [ ] API 文档（Swagger 自动导出 PDF）

- [ ] 用户手册（Markdown→HTML）

- [ ] 部署手册（含脚本、监控、备份）

 13.3 测试交付

- [ ] 单元测试覆盖率 ≥ 80%

- [ ] 并发压测报告（locust 导出）

- [ ] 种子用户验收通过（5 人）

 13.4 运维交付

- [ ] 自动备份脚本验证

- [ ] 健康检查接口 /api/health 200

- [ ] 日志轮转 + 告警邮件测试

 13.5 版本交付

- [ ] Git Tag v1.0 打版

- [ ] Release Notes 发布

 14. 一键生成脚本（给大模型直接输出）

 14.1 生成目录结构

bash

mkdir -p quant_web/{api/v1,core/{dm,sm,be,re,vis,sys},models,tests/{unit,integration,perf},scripts,docs,data,backup}

 14.2 生成常量文件

python

 quant_web/core/const.py

```python
AK_SLEEP = 0.5
```

```python
MAX_RETRY = 3
```

```python
SLIP_RANGE = (-0.01, 0.01)
```

```python
MAX_DD_THRESHOLD = 0.2
```

```python
WORKER_MAX_MEM = 2_000_000_000
```

```python
BATCH_SIZE = 1000
```

```python
QUALITY_SCORE_MIN = 60
```

```python
FACTOR_WEIGHTS = {"return": 0.4, "stability": 0.3, "active": 0.2, "quality": 0.1}
```

 14.3 生成 main.py（完整）

python

 quant_web/main.py

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
```

```python
from api.v1 import data, strategy, backtest, recommend
```

```python
from core.common.logger import setup_logger
```

```python
from core.const import MAX_DD_THRESHOLD
```

```python
import uvicorn
```

```python
setup_logger()
```

```python
app = FastAPI(title="QuantWeb", version="v1.0")
```

```python
app.include_router(data.router, prefix="/api/v1")
```

```python
app.include_router(strategy.router, prefix="/api/v1")
```

```python
app.include_router(backtest.router, prefix="/api/v1")
```

```python
app.include_router(recommend.router, prefix="/api/v1")
```

```python
@app.websocket("/ws/{task_id}")
```

```python
async def websocket_endpoint(websocket: WebSocket, task_id: str):
```

```python
await websocket.accept()
```

```python
Redis PubSub 简化版
```

```python
while True:
```

```python
try:
```

```python
msg = await redis.pubsub.get_message(ignore_subscribe_messages=True)
```

```python
if msg:
```

```python
await websocket.send_json(json.loads(msg["data"]))
```

```python
except WebSocketDisconnect:
```

```python
break
```

```python
if __name__ == "__main__":
```

```python
uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=4)
```

 14.4 生成 Dockerfile

dockerfile

```python
FROM python:3.11-slim
```

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

 14.5 生成 requirements.txt（锁定）

fastapi==0.110.0

uvicorn[standard]==0.27.0

sqlalchemy==2.0.23

alembic==1.13.1

redis==5.0.1

celery==5.3.4

pandas==2.1.4

numpy==1.26.2

akshare==1.11.1

tushare==1.3.0

loguru==0.7.2

pytest==7.4.3

pytest-cov==4.1.0

locust==2.20.1

 14.6 生成 run.bat（Windows 一键启动）

bat

@echo off

echo [QuantWeb] Starting...

start http://localhost:8000

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

 14.7 生成 run.sh（Linux/Mac 一键启动）

bash

!/bin/bash

echo "[QuantWeb] Starting..."

open http://localhost:8000

python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

 14.8 生成 CI/CD 文件

yaml

 .github/workflows/ci.yml

name: ci

on: [push]

jobs:

  build:

```python
runs-on: ubuntu-latest
```

```python
steps:
```

```python
- uses: actions/checkout@v3
```

```python
- uses: actions/setup-python@v4
```

```python
with: {python-version: '3.11'}
```

```python
- run: pip install -r requirements.txt
```

```python
- run: pip-audit
```

```python
- run: pytest --cov=80 --cov-report=xml
```

```python
- run: locust -f tests/perf/locustfile.py --headless -u 10 -r 2 -t 30s --csv=perf
```

```python
- run: docker build -t quant-web .
```

 15. 最终交付物清单（给大模型一次性生成）

1. 完整目录结构（14.1）

2. 全部 Python 源码（main.py、各模块、常量、函数原型、分支、异常）

3. 全部 SQL DDL（分区+索引+约束）

4. 全部接口规范（URL+请求+响应+错误码+示例）

5. 全部前端 Vue3 组件（Monaco+ECharts+WebSocket）

6. 全部测试用例（pytest+locust）

7. 全部运维脚本（run.bat/sh、Docker、CI/CD、备份）

8. 全部文档（API Swagger、用户手册、部署手册）

 16. 最终 Prompt 语句（给大模型）

请依据以上内容，一次性生成完整、可运行、零歧义的「个人量化投研 Web 平台」全部源代码、SQL、Docker、文档、测试、运维脚本，并确保：

1. 所有函数、字段、常量、路径、命名、错误码与本文档完全一致；

2. 所有分支、异常、重试、滑点、权重、公式与本文档完全一致；

3. 所有测试用例、性能门禁、CI/CD、上线清单与本文档完全一致；

4. 生成后可直接 `docker-compose up` 运行，浏览器访问 `http://localhost:8000` 即可使用全部功能。

确保：

- 所有常量、字段、路径、命名、错误码与文档完全一致；

- 所有分支、异常、重试、滑点、权重、公式与文档完全一致；

- 所有测试用例、性能门禁、CI/CD、上线清单与文档完全一致；

- 生成后无需人工修改任何文件。

 个人量化投研 Web 平台  

 大模型直接开发版补充文档（v6.0-Final）

更新：2024-01-27  

目的：补充前端完整原型、SQL文件、运维脚本、测试文件、CI/CD、文档模板，确保大模型零歧义一次性生成完整工程。

 目录

1. 前端完整原型（组件+配置+路由+Store）  

2. SQL 完整文件（init+seed+分区+索引）  

3. 运维完整脚本（备份+恢复+健康+升级）  

4. 测试完整文件（pytest+locust+fixtures）  

5. Docker 完整文件（compose+env+Dockerfile）  

6. CI/CD 完整文件（CI+CD+Release）  

7. 文档完整文件（用户+部署+API+验收）  

8. 最终目录树（文件级清单）  

9. 最终 Prompt（给大模型）

 1. 前端完整原型（Vue3 + TS + Vite）

 1.1 目录树（前端）

frontend/

├── public/

│   └── favicon.ico

├── src/

│   ├── api/                     Axios 封装

│   │   ├── data.ts

│   │   ├── strategy.ts

│   │   ├── backtest.ts

│   │   └── recommend.ts

│   ├── components/

│   │   ├── DataManager.vue

│   │   ├── StrategyEditor.vue

│   │   ├── BacktestForm.vue

│   │   ├── ReportViewer.vue

│   │   └── RecommendList.vue

│   ├── router/

│   │   └── index.ts

│   ├── stores/

│   │   ├── index.ts

│   │   ├── websocket.ts

│   │   └── theme.ts

│   ├── App.vue

│   ├── main.ts

│   └── style.css

├── package.json

├── vite.config.ts

└── tsconfig.json

 1.2 主要文件内容（直接生成）

 （1）main.ts

typescript

```python
import { createApp } from 'vue';
```

```python
import App from './App.vue';
```

```python
import router from './router';
```

```python
import { createPinia } from 'pinia';
```

```python
import ElementPlus from 'element-plus';
```

```python
import 'element-plus/dist/index.css';
```

```python
import 'monaco-editor/esm/vs/basic-languages/python/python.contribution';
```

```python
const app = createApp(App);
```

```python
app.use(createPinia());
```

```python
app.use(router);
```

```python
app.use(ElementPlus);
```

```python
app.mount('app');
```

 （2）App.vue

vue

<template>

  <el-container>

```python
<el-header>
```

```python
<el-menu mode="horizontal" :router="true">
```

```python
<el-menu-item index="/">首页</el-menu-item>
```

```python
<el-menu-item index="/data">数据管理</el-menu-item>
```

```python
<el-menu-item index="/strategy">策略编辑</el-menu-item>
```

```python
<el-menu-item index="/backtest">回测</el-menu-item>
```

```python
<el-menu-item index="/recommend">推荐</el-menu-item>
```

```python
</el-menu>
```

```python
</el-header>
```

```python
<el-main>
```

```python
<router-view />
```

```python
</el-main>
```

  </el-container>

</template>

 （3）StrategyEditor.vue（Monaco 完整配置）

vue

<template>

  <div class="strategy-editor">

```python
<MonacoEditor
```

```python
ref="editor"
```

```python
v-model="code"
```

```python
language="python"
```

```python
:theme="theme"
```

```python
:options="editorOptions"
```

```python
style="height: 600px"
```

```python
/>
```

```python
<el-button type="primary" @click="save">保存</el-button>
```

  </div>

</template>

<script setup lang="ts">

```python
import { ref } from 'vue';
```

```python
import MonacoEditor from 'monaco-editor-vue3';
```

```python
import { saveStrategy } from '@/api/strategy';
```

```python
const code = ref(`import talib
```

```python
g_params = {"fast": 5, "slow": 20}
```

```python
def handle_data(context):
```

```python
pass`);
```

```python
const theme = ref('vs-dark');
```

```python
const editorOptions = {
```

  fontSize: 14,

  minimap: { enabled: false },

  scrollBeyondLastLine: false,

  wordWrap: 'on'

};

```python
async function save() {
```

```python
await saveStrategy({ name: 'MyStrategy', code: code.value });
```

```python
ElMessage.success('已保存');
```

}

</script>

 （4）router/index.ts

typescript

```python
import { createRouter, createWebHistory } from 'vue-router';
```

```python
const routes = [
```

  { path: '/', redirect: '/data' },

```python
{ path: '/data', component: () => import('@/components/DataManager.vue') },
```

```python
{ path: '/strategy', component: () => import('@/components/StrategyEditor.vue') },
```

```python
{ path: '/backtest', component: () => import('@/components/BacktestForm.vue') },
```

```python
{ path: '/recommend', component: () => import('@/components/RecommendList.vue') }
```

];

```python
export default createRouter({ history: createWebHistory(), routes });
```

 （5）stores/websocket.ts

typescript

```python
import { defineStore } from 'pinia';
```

```python
import { ref } from 'vue';
```

```python
export const useWebSocketStore = defineStore('ws', () => {
```

```python
const socket = ref<WebSocket | null>(null);
```

```python
const logs = ref<string[]>([]);
```

```python
function connect(taskId: string) {
```

```python
socket.value = new WebSocket(`ws://localhost:8000/ws/${taskId}`);
```

```python
socket.value.onmessage = (e) => logs.value.push(e.data);
```

  }

  return { connect, logs };

});

 （6）package.json（锁定版本）

json

{

  "name": "quant-web-frontend",

  "version": "1.0.0",

  "scripts": {

```python
"dev": "vite",
```

```python
"build": "vite build",
```

```python
"preview": "vite preview"
```

  },

  "dependencies": {

```python
"vue": "^3.4.0",
```

```python
"vue-router": "^4.2.5",
```

```python
"pinia": "^2.1.7",
```

```python
"element-plus": "^2.4.4",
```

```python
"monaco-editor-vue3": "^0.1.10",
```

```python
"axios": "^1.6.2"
```

  },

  "devDependencies": {

```python
"@vitejs/plugin-vue": "^4.5.2",
```

```python
"typescript": "^5.3.3",
```

```python
"vite": "^5.0.10"
```

  }

}

 2. SQL 完整文件

 2.1 init.sql（SQLite 语法）

sql

- - 股票列表

```python
CREATE TABLE stock_basic (
```

```python
ts_code TEXT PRIMARY KEY,
```

```python
symbol TEXT NOT NULL,
```

```python
name TEXT NOT NULL,
```

```python
area TEXT,
```

```python
industry TEXT,
```

```python
list_date TEXT,
```

```python
data_source TEXT DEFAULT 'akshare' CHECK(data_source IN ('akshare','tushare')),
```

```python
status INTEGER DEFAULT 1 CHECK(status IN (0,1)),
```

```python
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

);

```python
CREATE INDEX idx_sb_industry ON stock_basic(industry);
```

- - 策略元数据

```python
CREATE TABLE strategy (
```

```python
id TEXT PRIMARY KEY,
```

```python
name TEXT NOT NULL,
```

```python
code TEXT NOT NULL,
```

```python
params_json TEXT,
```

```python
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
```

```python
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
```

```python
version INTEGER DEFAULT 1
```

);

- - 回测任务

```python
CREATE TABLE backtest_task (
```

```python
id TEXT PRIMARY KEY,
```

```python
strategy_id TEXT NOT NULL,
```

```python
stock_pool TEXT NOT NULL, -- JSON 数组
```

```python
start_date TEXT NOT NULL,
```

```python
end_date TEXT NOT NULL,
```

```python
init_cash REAL NOT NULL,
```

```python
status TEXT CHECK(status IN ('Pending','Running','Success','Failed')),
```

```python
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
```

```python
report_path TEXT
```

);

- - 推荐结果

```python
CREATE TABLE recommend_result (
```

```python
id TEXT PRIMARY KEY,
```

```python
task_id TEXT NOT NULL,
```

```python
trade_date TEXT NOT NULL,
```

```python
rank INTEGER NOT NULL,
```

```python
ts_code TEXT NOT NULL,
```

```python
score REAL NOT NULL,
```

```python
reason TEXT,
```

```python
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

);

```python
CREATE INDEX idx_rec_task ON recommend_result(task_id);
```

 2.2 seed.sql（初始数据）

sql

- - 12 策略模板

```python
INSERT INTO strategy (id, name, code, params_json) VALUES
```

```python
('tpl_ma', '双均线', 'import talib\ng_params={"fast":5,"slow":20}\ndef handle_data(ctx):\n    for stock in ctx.stocks:\n        close = Close(stock)\n        if len(close) < g_params["slow"]: continue\n        ma_fast = talib.MA(close, g_params["fast"])\n        ma_slow = talib.MA(close, g_params["slow"])\n        if ma_fast[-1] > ma_slow[-1] and MarketPosition(stock) == 0:\n            Buy(stock, 100, close[-1])\n        elif ma_fast[-1] < ma_slow[-1] and MarketPosition(stock) > 0:\n            Sell(stock, 100, close[-1])', '{"fast":5,"slow":20}');
```

- - 示例股票（平安银行、浦发银行）

```python
INSERT INTO stock_basic (ts_code, symbol, name, industry) VALUES
```

```python
('000001.SZ', '000001', '平安银行', '银行'),
```

```python
('600000.SH', '600000', '浦发银行', '银行');
```

 2.3 migrate.sh（一键迁移）

bash

!/bin/bash

set -e

echo "[Migrate] Start..."

alembic upgrade head

echo "[Migrate] Done."

 3. 运维完整脚本

 3.1 backup.sh（完整备份）

bash

!/bin/bash

set -e

```python
DATE=$(date +%F)
```

BACKUP_DIR="./backup"

mkdir -p $BACKUP_DIR

tar -zcf $BACKUP_DIR/quant_$DATE.tar.gz ./data ./logs

aws s3 cp $BACKUP_DIR/quant_$DATE.tar.gz s3://your-bucket/backup/ || echo "S3 未配置，保留本地"

echo "[Backup] 完成 $BACKUP_DIR/quant_$DATE.tar.gz"

 3.2 health_check.sh

bash

!/bin/bash

set -e

```python
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
```

```python
MEM=$(free | grep Mem | awk '{printf("%.1f", $3/$2  100.0)}')
```

```python
DISK=$(df ./data | tail -1 | awk '{print $5}' | cut -d'%' -f1)
```

```python
if (( $(echo "$CPU > 80" | bc -l) )) || (( $(echo "$MEM > 80" | bc -l) )) || [ $DISK -gt 80 ]; then
```

  echo "ALERT: CPU=$CPU% MEM=$MEM% DISK=$DISK%" | mail -s "QuantWeb 告警" admin@example.com

fi

 3.3 upgrade.sh

bash

!/bin/bash

set -e

echo "[Upgrade] 开始备份..."

./backup.sh

echo "[Upgrade] 停止服务..."

docker-compose down

echo "[Upgrade] 拉取最新镜像..."

docker-compose pull

echo "[Upgrade] 数据库迁移..."

docker-compose run --rm web alembic upgrade head

echo "[Upgrade] 启动服务..."

docker-compose up -d

echo "[Upgrade] 完成。"

 4. 测试完整文件

 4.1 tests/unit/test_dm.py

python

```python
import asyncio
```

```python
from quant_web.core.dm.akshare_adapter import AkShareAdapter
```

```python
def test_download_daily():
```

```python
adapter = AkShareAdapter()
```

```python
df = asyncio.run(adapter.download_daily("000001.SZ", "20230101", "20231231"))
```

```python
assert len(df) >= 240
```

```python
assert df.isnull().sum().sum() == 0
```

 4.2 tests/integration/test_backtest.py

python

```python
import asyncio
```

```python
from quant_web.api.v1.backtest import submit_backtest
```

```python
from quant_web.core.be.engine import BacktestEngine
```

```python
def test_backtest_flow():
```

```python
req = {
```

```python
"strategy_id": "tpl_ma",
```

```python
"stock_pool": ["000001.SZ"],
```

```python
"start_date": "20230101",
```

```python
"end_date": "20231231",
```

```python
"init_cash": 100000,
```

```python
"params": {"fast": 5, "slow": 20}
```

```python
}
```

```python
resp = asyncio.run(submit_backtest(req))
```

```python
assert resp["task_id"].startswith("BK_")
```

 4.3 tests/perf/locustfile.py

python

```python
from locust import HttpUser, task, between
```

```python
class QuantUser(HttpUser):
```

```python
wait_time = between(1, 3)
```

```python
@task
```

```python
def submit_backtest(self):
```

```python
self.client.post("/api/v1/backtest/submit", json={
```

```python
"strategy_id": "tpl_ma",
```

```python
"stock_pool": ["000001.SZ"],
```

```python
"start_date": "20230101",
```

```python
"end_date": "20231231",
```

```python
"init_cash": 100000,
```

```python
"params": {"fast": 5, "slow": 20}
```

```python
})
```

 5. Docker 完整文件

 5.1 Dockerfile

dockerfile

```python
FROM python:3.11-slim
```

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

 5.2 docker-compose.yml

yaml

version: "3.8"

services:

  web:

```python
build: .
```

```python
ports: ["8000:8000"]
```

```python
env_file: .env
```

```python
depends_on: [redis]
```

```python
volumes: ["./data:/app/data", "./logs:/app/logs"]
```

  redis:

```python
image: redis:7-alpine
```

```python
ports: ["6379:6379"]
```

```python
volumes: ["redis_data:/data"]
```

  worker:

```python
build: .
```

```python
command: celery -A tasks worker --loglevel=info --concurrency=4
```

```python
depends_on: [redis]
```

```python
volumes: ["./data:/app/data", "./logs:/app/logs"]
```

volumes:

  redis_data:

 5.3 .env.example

 数据库

DATABASE_URL=sqlite:///./data/quant.db

 Redis

REDIS_URL=redis://redis:6379/0

 JWT（可选）

JWT_SECRET=your-secret

 SMTP（可选）

SMTP_HOST=smtp.example.com

SMTP_PORT=587

SMTP_USER=admin@example.com

SMTP_PASS=your-password

 6. CI/CD 完整文件

 6.1 .github/workflows/ci.yml

yaml

name: CI

on: [push]

jobs:

  build:

```python
runs-on: ubuntu-latest
```

```python
steps:
```

```python
- uses: actions/checkout@v3
```

```python
- uses: actions/setup-python@v4
```

```python
with: {python-version: '3.11'}
```

```python
- run: pip install -r requirements.txt
```

```python
- run: pip-audit
```

```python
- run: pytest --cov=80 --cov-report=xml
```

```python
- run: locust -f tests/perf/locustfile.py --headless -u 10 -r 2 -t 30s --csv=perf
```

```python
- run: docker build -t quant-web .
```

 6.2 .github/workflows/cd.yml

yaml

name: CD

on:

  push:

```python
tags: ["v"]
```

jobs:

  deploy:

```python
runs-on: ubuntu-latest
```

```python
steps:
```

```python
- uses: actions/checkout@v3
```

```python
- run: docker-compose down
```

```python
- run: docker-compose pull
```

```python
- run: docker-compose up -d
```

 6.3 .github/workflows/release.yml

yaml

name: Release

on:

  push:

```python
tags: ["v"]
```

jobs:

  release:

```python
runs-on: ubuntu-latest
```

```python
steps:
```

```python
- uses: actions/checkout@v3
```

```python
- run: docker build -t quant-web:${GITHUB_REF_NAME} .
```

```python
- run: echo "Release ${GITHUB_REF_NAME}" >> release_notes.md
```

```python
- uses: softprops/action-gh-release@v1
```

```python
with:
```

```python
files: release_notes.md
```

```python
tag_name: ${{ github.ref_name }}
```

 7. 文档完整文件

 7.1 docs/user_manual.md

markdown

 用户手册

 1. 快速开始

1. 浏览器访问 http://localhost:8000

2. 点击“数据管理”→选择股票→下载

3. 点击“策略编辑”→选择模板→保存

4. 点击“回测”→提交任务→查看报告

5. 点击“推荐”→生成 Top-N 列表

 7.2 docs/deploy.md

markdown

 部署手册

 Docker 一键部署

bash

docker-compose up -d

访问 http://localhost:8000

 7.3 docs/api.md

markdown

 API 文档

```python
[Swagger UI](http://localhost:8000/docs)
```

 7.4 docs/acceptance_report.md

markdown

 验收报告

- 功能：✅ 全部通过

- 性能：✅ P95 ≤ 500ms

- 并发：✅ 3 任务无崩溃

- 备份：✅ 演练成功

验收人：_________ 日期：_________

 8. 最终目录树（文件级清单）

quant_web/

├── main.py

├── requirements.txt

├── Dockerfile

├── docker-compose.yml

├── .env.example

├── api/v1/

│   ├── data.py

│   ├── strategy.py

│   ├── backtest.py

│   └── recommend.py

├── core/

│   ├── const.py

│   ├── dm/akshare_adapter.py

│   ├── sm/syntax_checker.py

│   ├── be/matcher.py

│   ├── re/factor_model.py

│   └── vis/report_generator.py

├── models/database.py

├── tasks.py

├── tests/

│   ├── unit/test_dm.py

│   ├── integration/test_backtest.py

│   └── perf/locustfile.py

├── scripts/

│   ├── run.bat

│   ├── run.sh

│   ├── backup.sh

│   ├── restore.sh

│   ├── health_check.sh

│   └── upgrade.sh

├── docs/

│   ├── user_manual.md

│   ├── deploy.md

│   ├── api.md

│   └── acceptance_report.md

├── .github/workflows/

│   ├── ci.yml

│   ├── cd.yml

│   └── release.yml

├── sql/

│   ├── init.sql

│   ├── seed.sql

│   └── migrate.sh

frontend/

├── package.json

├── vite.config.ts

├── src/

│   ├── main.ts

│   ├── App.vue

│   ├── router/index.ts

│   ├── stores/websocket.ts

│   ├── components/StrategyEditor.vue

│   ├── components/DataManager.vue

│   ├── components/BacktestForm.vue

│   ├── components/ReportViewer.vue

│   └── components/RecommendList.vue

 9. 最终 Prompt（给大模型）

请依据以上全部内容（v6.0-Final），一次性生成完整、可运行、零歧义的「个人量化投研 Web 平台」全部源代码、SQL、Docker、文档、测试、运维脚本，并确保：

1. 所有常量、字段、路径、命名、错误码与文档完全一致；

2. 所有分支、异常、重试、滑点、权重、公式与文档完全一致；

3. 所有测试用例、性能门禁、CI/CD、上线清单与文档完全一致；

4. 生成后执行 `docker-compose up` 即可访问 http://localhost:8000 使用全部功能；

5. 生成完毕后输出：目录树（前 20 文件）+ 一键启动命令。

禁止遗漏任何文件；禁止出现任何 TODO 或占位符；禁止需要人工修改。

要让大模型（或一个工程团队）真正零歧义、一次性地生成出这份文档所描述的「个人量化投研 Web 平台」可运行完整系统，文档还需要补充以下 8 大类、共 60+ 项“最后一公里”细节。缺任何一项，都会导致“看起来都写了，一跑就报错”。

 1. 运行时依赖：版本 & 安装源

| 缺什么 | 补充到什么粒度 | 示例 |

| Python 解释器版本 | 精确到 patch | `python 3.11.7`（3.11.8 起 numpy 1.26.2 会编译警告） |

| Node 版本 | `.nvmrc` 文件 | `18.19.0`（vite 5.0.10 最低） |

| 系统级库 | apt/yum 列表 | `libgomp1`、`libhdf5-serial-dev`（akshare 依赖） |

| 国内源 | 完整 pip 镜像 | `-i https://pypi.tuna.tsinghua.edu.cn/simple` |

| pnpm/npm 源 | `.npmrc` | `registry=https://registry.npmmirror.com` |

 2. 前端构建流水线

| 缺什么 | 补充到什么粒度 | 示例 |

| 构建脚本 | 精确命令 | `npm run build` 产物 `dist/` 被 `nginx:alpine` 镜像托管 |

| 环境变量 | 枚举 | `VITE_API_BASE=http://localhost:8000/api/v1` |

| 类型检查 | `vue-tsc --noEmit` | CI 门禁必须过 |

| 包体积门禁 | `bundlesize` | `dist/assets/.js ≤ 800 kB` gzip |

| 浏览器兼容 | `.browserslistrc` | `> 1%, last 2 years, not dead` |

 3. 数据库“空表”初始状态

| 缺什么 | 补充到什么粒度 | 示例 |

| SQLite 文件已存在场景 | 冲突策略 | `alembic stamp head` 前先 `quant.db` md5 校验 |

| MySQL 切库 | 字符集 & 时区 | `charset=utf8mb4 collate=utf8mb4_0900_ai_ci` `SET time_zone='+8:00'` |

| 种子数据 idempotent | `INSERT OR IGNORE` | 重复执行不抛主键冲突 |

```python
| 分区表自动扩展 | 事件调度 | 2025 新表 `PARTITION p2025 VALUES LESS THAN (2026)` 由 `sys_event` 提前创建 |
```

 4. 策略沙箱“白名单” & 注入 API

| 缺什么 | 补充到什么粒度 | 示例 |

```python
| 允许 import 清单 | 精确到模块级 | `numpy`, `pandas`, `talib`, `scipy.stats`, `sklearn.preprocessing` |
```

```python
| 注入函数签名 | 类型注解 | `def Buy(ts_code: str, qty: int, price: float) -> str:` |
```

```python
| 全局变量生命周期 | 说明文档 | `g_params` 在 `initialize()` 时注入，回测结束回收 |
```

```python
| 禁止语法 | AST 黑名单 | `import ast; ast.Name(id='open')` 触发 `SyntaxError` |
```

```python
| 超时控制 | 子进程 | `resource.setrlimit(RLIMIT_CPU, (3060, 3060))` |
```

 5. 错误码 & 重试矩阵

| 缺什么 | 补充到什么粒度 | 示例 |

| 业务错误码表 | 唯一 5 位数字 | `40001` 日期格式错，`40002` 股票代码不存在 |

```python
| 重试策略 | 指数退避公式 | `sleep = base  2attempt + random.uniform(0, 1)` |
```

| 熔断阈值 | 可观测指标 | 连续 5 次 `40002` 触发 15 min 熔断，停用该数据源 |

| 用户提示文案 | 多语言 | `zh-CN`：“起始日期不能大于今日” |

 6. 日志规范 & 可观测

| 缺什么 | 补充到什么粒度 | 示例 |

| 日志格式 | JSON schema | `{"t":"2025-06-01T12:00:00.000Z","lvl":"INFO","trace_id":"bk_123","mod":"be.matcher","msg":"trade executed","extra":{"price":10.12}}` |

| 日志采样 | 配置开关 | 高并发时只采样 10% `INFO`，`ERROR` 全采 |

| 度量指标 | Prometheus | `backtest_duration_seconds{strategy_id="tpl_ma"}` Counter |

| 链路追踪 | OpenTelemetry | `traceparent` 透传 headers |

 7. 测试 fixtures & 种子数据

| 缺什么 | 补充到什么粒度 | 示例 |

| 最小可运行数据集 | CSV | `000001.SZ 2023-01-03 ~ 2023-01-10` 8 条日线，含权息 |

| mock 外部数据源 | `pytest-httpx` | AkShare 返回 HTML 504 时走 `respx.MockRouter` |

| 性能基线文件 | `.pkl` | 把 1 年 000001 预期结果序列化，单元测试断言误差 `< 1e-4` |

| 并发压测场景 | `locustfile.py` | 10 用户各提交 3 任务，Ramp-up 30 s，Hold 60 s |

 8. 一键脚本“幂等 & 回滚”

| 缺什么 | 补充到什么粒度 | 示例 |

| 安装脚本 | 幂等检测 | `if [[ -f .installed ]] ; then echo "Skip pip install"; fi` |

| 升级回滚 | 数据库版本 | `alembic downgrade -1` 自动触发 `quant.db.backup` |

| 数据目录权限 | 数字模式 | `chmod 750 ./data ./logs; chown 1000:1000`（容器内 uid） |

| Windows 长路径 | `\\?\` 前缀 | `robocopy` 替代 `cp` 防止 260 字符溢出 |

| 卸载脚本 | 清理列表 | 删除镜像、卷、本地 `~/.quant-web` 配置目录 |

 📌 交付 checklist（补充完毕后）

- [ ] 提供 `complete-v6.1.zip` → 解压 → `docker-compose up` → 浏览器 `http://localhost:8000` 直接看到登录后首页

- [ ] 单元测试 `pytest` 100% 通过，无 skipped

- [ ] 前端 `npm run build` 通过且 bundle ≤ 800 kB

- [ ] 压测 `locust -u 10 -t 60s` 错误率 0%，P95 ≤ 500 ms

```python
- [ ] 策略沙箱执行 `import os` 立即抛 `SyntaxError: illegal import`
```

- [ ] 升级脚本 `./scripts/upgrade.sh v1.0 v1.1` 回滚后数据库行数一致

 ✅ 结论

只有把上述 60+ 项“颗粒度”全部文档化、脚本化、门禁化，大模型才能一次性吐出可运行、零人工修复的量化系统。  

换句话说：

> 文档的终点不是“讲清楚”，而是“机器能一次性复制成功”。

 必须确认项清单（用于生成可直接运行的 QuantWeb 工程）

更新：2025-11-10

目的：把之前会话中识别出的“高风险/必须确认”的配置项以清单形式写入仓库，便于你逐项确认或接受默认值，以便我继续生成完整工程骨架。

说明：每一项包含：要确认的内容 / 建议默认值 / 为什么必须确认 / 若不确认的风险。

 高优先级（必须立即确认）

1. Python 精确版本

   - 要确认：主机与 Docker 中使用的 Python 精确版本（含 patch）

   - 建议：`3.11.7`

   - 原因：部分依赖（如 numpy/pandas/akshare）对 Python patch 版本敏感，影响二进制兼容

   - 风险：依赖安装失败或运行时异常，导致无法直接 `docker-compose up`。

2. Node / npm / pnpm 版本（前端）

   - 要确认：Node 版本与包管理器（并加入 `.nvmrc`）

   - 建议：`Node 18.19.0`，使用 `npm` 或 `pnpm`（请选择其一）

   - 原因：Vite 与某些前端依赖对 Node 版本有最低要求

   - 风险：前端构建失败，影响整体交付

3. 系统级库（Docker 基础镜像所需）

   - 要确认：是否在 Dockerfile 中安装 `libgomp1`, `libhdf5-serial-dev`, `build-essential` 等

   - 建议：在 Dockerfile 中安装常见系统依赖并提供注释

   - 原因：akshare / numpy 等可能需要本地系统库支持

   - 风险：`pip install` 编译/运行失败

4. 数据库选择与迁移策略

   - 要确认：默认使用 SQLite 还是 MySQL 以及 alembic 在已存在 DB 的行为

   - 建议：默认 `SQLite`（`sqlite:///./data/quant.db`），同时文档中说明 MySQL 配置；迁移前自动备份 `quant.db`。

   - 原因：DDL 文档包含 MySQL 专用分区语句，需区分运行时 DB 类型

   - 风险：在 SQLite 上执行 MySQL DDL 导致迁移失败或数据丢失

5. 策略沙箱白名单与资源限制

   - 要确认：允许策略 `import` 的模块清单、禁止语法、单策略超时时间、内存上限实现方式

   - 建议白名单：`numpy, pandas, talib, math, statistics`；超时 30 分钟；内存限制 2GB（子进程 + `resource.setrlimit`）

   - 原因：策略可执行任意 Python，必须防止越权访问与资源耗尽

   - 风险：平台被恶意或错误策略破坏、数据泄露或服务不可用

6. 业务错误码完整表

   - 要确认：全部业务错误码（5 位）与对应前端文案

   - 建议：保留 `40001..40100` 范围用于常见输入/业务错误，并在文档中列举已用码

   - 原因：前端/测试/日志需一致的错误码以便断言与用户提示

   - 风险：测试断言失败或前端提示混乱

 中优先级（开发阶段需确认）

7. 种子数据与幂等导入策略

   - 要确认：seed.sql 是否采用 `INSERT OR IGNORE` 或 idempotent 脚本；提供最小测试数据集

   - 建议：提供最小 CSV（1 支股票 8~10 条日线）用于 CI；seed 使用 `INSERT OR IGNORE`

   - 风险：重复导入主键冲突或测试不稳定

8. 外部服务凭据与 `.env` 策略

   - 要确认：SMTP、S3、TUSHARE key 等是否放入 `.env`，以及缺失时的优雅降级策略

   - 建议：保留 `.env.example`，运行时缺省值导致功能禁用并记录日志告警

   - 风险：部署环境因凭据缺失崩溃

9. 前端 API 基础路径与构建环境变量

   - 要确认：`VITE_API_BASE` 的默认值与容器内后端主机名

   - 建议：开发 `http://localhost:8000/api/v1`，docker-compose 内使用 `http://web:8000/api/v1`

   - 风险：跨域/CORS 或前端请求失败

10. 日志格式、采样与追踪策略

```python
- 要确认：是否启用 JSON 日志、Prometheus、OpenTelemetry
```

```python
- 建议：JSON 日志（loguru），关键度量 Prometheus（后续扩展）
```

```python
- 风险：缺少可观测性，故障排查困难
```

11. 备份/恢复与 S3 配置

```python
- 要确认：备份频率、保留天数与 S3 桶信息
```

```python
- 建议：默认本地每日备份 7 天保留；S3 为可选需在 `.env` 填写凭据
```

```python
- 风险：数据无法恢复
```

 低优先级（迭代确认即可）

12. 前端构建门禁（类型检查、bundle 大小）

```python
- 建议：CI 强制 `vue-tsc --noEmit`，bundle gzip 限制（例如 ≤ 800 KB）
```

13. CI 性能测试阈值

```python
- 建议：CI 做轻量 locust 快照（10 users, 30s），重负载场景单独流水线
```

14. Alembic 与分区表策略

```python
- 建议：迁移脚本根据 `DATABASE_URL` 判断 DB 类型并选择相应 DDL
```

15. 告警接收人（邮件）

```python
- 建议：`.env` 中配置 `ADMIN_EMAILS`，缺失则仅记录日志
```

16. CORS 策略

```python
- 建议：开发环境允许 ``，生产环境通过 `.env` 指定白名单
```

17. Docker 资源限制与重启策略

```python
- 建议：为 `web`/`worker` 设置内存限制（例如 2g）和 `restart: unless-stopped`
```

18. 用户认证方式

```python
- 建议：默认单用户 `local_user` 简化部署；提供可选 JWT（由 `.env` 打开）
```

19. 重试与熔断策略

```python
- 建议：指数退避 `sleep = base  2attempt + random(0,1)`；连续 5 次同类错误熔断 15 分钟
```

20. 最小测试 fixtures

```python
- 建议：提供最小 CSV/JSON kline 数据供 pytest fixtures 使用
```

 下一步与操作选项

请选择：

- 在此会话逐项确认（我将按你的确认生成工程） — 回复示例：`确认 Python=3.11.7, Node=18.19.0, 使用 SQLite, 允许 talib`。

- 接受文档中的默认建议并继续生成完整骨架 — 回复 `默认并继续`。

- 或要求对某一项先生成示例实现/脚本 — 比如 `先实现沙箱` 或 `先实现 Alembic 分支迁移`

文件路径：`docs/confirm_items.md`

作者工具自动生成（来自需求文档分析）。