# QuantWeb — skeleton

这是一个个人量化投研 Web 平台的骨架实现，用于快速验证架构与端到端流程的最小可运行示例。

快速启动（本地）
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn quant_web.main:app --reload
```

或使用 docker-compose
```bash
docker-compose up --build
```

API:
- GET /api/v1/health
- POST /api/v1/data/download
- POST /api/v1/backtest/submit
- ws  /ws/{task_id}




谢谢