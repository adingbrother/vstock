from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field
import asyncio
from datetime import datetime
from typing import Optional

from quant_web.core.tasks import start_backtest_task
from quant_web.core.task_manager import global_task_manager

router = APIRouter()


class StrategyConfig(BaseModel):
    """策略配置模型"""
    name: str = Field(..., description="策略名称")
    parameters: dict = Field(default_factory=dict, description="策略参数")


class BacktestRequest(BaseModel):
    """回测请求模型"""
    strategy_config: StrategyConfig = Field(..., description="策略配置")
    stock_pool: list[str] = Field(..., description="股票池")
    start_date: str = Field(..., description="开始日期，格式：YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期，格式：YYYY-MM-DD")
    init_cash: Optional[float] = Field(default=1000000.0, description="初始资金")


@router.post("/backtest/submit", status_code=202)
async def submit_backtest(req: BacktestRequest, background_tasks: BackgroundTasks):
    """提交回测任务"""
    # 生成任务ID
    task_id = f"BK_{int(datetime.now().timestamp() * 1000)}"
    
    try:
        # 解析日期
        start_date = datetime.strptime(req.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(req.end_date, "%Y-%m-%d")
        
        # 创建消息队列
        queue = asyncio.Queue()
        
        # 将回测任务添加到后台任务
        background_tasks.add_task(
            start_backtest_task,
            task_id=task_id,
            strategy_config=req.strategy_config.model_dump(),
            stock_pool=req.stock_pool,
            start_date=start_date,
            end_date=end_date,
            queue=queue
        )
        
        # 返回任务ID和状态
        return {
            "task_id": task_id,
            "status": "Pending",
            "message": "回测任务已提交，正在处理中"
        }
    except Exception as e:
        return {
            "error": "提交回测任务失败",
            "message": str(e),
            "status_code": 400
        }


@router.get("/backtest/status/{task_id}")
async def get_backtest_status(task_id: str):
    """获取回测任务状态"""
    task = global_task_manager.get_task(task_id)
    
    if not task:
        return {
            "error": "任务不存在",
            "status_code": 404
        }
    
    # 返回任务信息
    return task.to_dict()


@router.get("/backtest/result/{task_id}")
async def get_backtest_result(task_id: str):
    """获取回测结果"""
    task = global_task_manager.get_task(task_id)
    
    if not task:
        return {
            "error": "任务不存在",
            "status_code": 404
        }
    
    # 检查任务状态
    if task.status.value not in ["completed", "failed"]:
        return {
            "error": "任务尚未完成",
            "status": task.status.value,
            "progress": task.progress,
            "status_code": 202
        }
    
    # 返回任务结果
    return {
        "task_id": task.task_id,
        "status": task.status.value,
        "result": task.result,
        "error": task.error,
        "progress": task.progress,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None
    }
