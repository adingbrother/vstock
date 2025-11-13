from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import asyncio
from loguru import logger

from quant_web.core.re.factor_model import FactorModel
from quant_web.core.const import FACTOR_WEIGHTS

# 模拟推荐任务存储
tasks: Dict[str, Dict] = {}
# 模拟推荐结果存储
recommendations: Dict[str, List[Dict]] = {}
# 初始化因子模型
factor_model = FactorModel()

router = APIRouter(
    prefix="/api/v1/recommend",
    tags=["recommend"],
    responses={404: {"description": "Not found"}},
)


class RecommendRequest(BaseModel):
    """推荐请求模型"""
    stock_pool: List[str] = Field(..., description="股票池列表")
    factors: Optional[Dict[str, float]] = Field(default=None, description="自定义因子权重")
    top_n: int = Field(default=10, ge=1, le=100, description="推荐数量")
    time_range: Optional[str] = Field(default="3m", description="时间范围")


class RecommendTask(BaseModel):
    """推荐任务模型"""
    task_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    request: RecommendRequest
    estimated_completion_time: Optional[float] = None


class RecommendResult(BaseModel):
    """推荐结果模型"""
    task_id: str
    stock_code: str
    ranking: int
    score: float
    trading_date: datetime
    factor_scores: Dict[str, float]
    description: Optional[str] = None


class FactorConfig(BaseModel):
    """因子配置模型"""
    name: str
    weight: float = Field(..., ge=0, le=1)
    description: Optional[str] = None


@router.post("/tasks", response_model=RecommendTask)
async def create_recommend_task(request: RecommendRequest, background_tasks: BackgroundTasks):
    """
    创建推荐任务
    
    - **stock_pool**: 待推荐的股票池列表
    - **factors**: 可选的自定义因子权重配置
    - **top_n**: 返回前N个推荐结果，默认10
    - **time_range**: 时间范围，默认3个月
    """
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 验证因子权重是否正确
        if request.factors:
            total_weight = sum(request.factors.values())
            if abs(total_weight - 1.0) > 0.001:
                raise HTTPException(status_code=400, detail="因子权重总和必须为1")
            
        # 创建任务
        task = {
            "task_id": task_id,
            "status": "pending",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "request": request.dict(),
            "estimated_completion_time": len(request.stock_pool) * 0.1  # 预估完成时间
        }
        
        tasks[task_id] = task
        
        # 添加后台任务
        background_tasks.add_task(run_recommend_algorithm, task_id, request)
        
        return RecommendTask(**task)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建推荐任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建推荐任务失败")


@router.get("/tasks/{task_id}", response_model=RecommendTask)
async def get_task_status(task_id: str):
    """获取推荐任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return RecommendTask(**tasks[task_id])


@router.get("/tasks/{task_id}/results", response_model=List[RecommendResult])
async def get_recommend_results(task_id: str):
    """获取推荐结果"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = tasks[task_id]
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")
    
    if task_id not in recommendations:
        raise HTTPException(status_code=404, detail="推荐结果不存在")
    
    return [RecommendResult(**result) for result in recommendations[task_id]]


@router.get("/factors", response_model=List[FactorConfig])
async def get_factor_configs():
    """获取当前因子配置"""
    return [
        FactorConfig(
            name=name,
            weight=weight,
            description=get_factor_description(name)
        )
        for name, weight in FACTOR_WEIGHTS.items()
    ]


@router.put("/factors/{factor_name}")
async def update_factor_weight(factor_name: str, weight: float):
    """更新因子权重"""
    if factor_name not in FACTOR_WEIGHTS:
        raise HTTPException(status_code=404, detail="因子不存在")
    
    if not 0 <= weight <= 1:
        raise HTTPException(status_code=400, detail="权重必须在0到1之间")
    
    # 这里只修改当前进程中的权重配置
    # 在实际应用中，可能需要更新配置文件或数据库
    original_weight = FACTOR_WEIGHTS[factor_name]
    FACTOR_WEIGHTS[factor_name] = weight
    
    # 调整其他因子的权重，确保总和为1
    weight_diff = weight - original_weight
    if weight_diff != 0:
        other_factors = [f for f in FACTOR_WEIGHTS if f != factor_name]
        if other_factors:
            weight_adjust = weight_diff / len(other_factors)
            for f in other_factors:
                FACTOR_WEIGHTS[f] -= weight_adjust
                # 确保权重不小于0
                FACTOR_WEIGHTS[f] = max(0, FACTOR_WEIGHTS[f])
    
    # 重新归一化所有权重
    total = sum(FACTOR_WEIGHTS.values())
    for f in FACTOR_WEIGHTS:
        FACTOR_WEIGHTS[f] = FACTOR_WEIGHTS[f] / total
    
    return {"message": f"因子 {factor_name} 的权重已更新为 {weight:.4f}"}


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_recommend_history(limit: int = 10, offset: int = 0):
    """获取推荐历史"""
    # 获取已完成的任务
    completed_tasks = [t for t in tasks.values() if t["status"] == "completed"]
    
    # 按创建时间倒序排序
    completed_tasks.sort(key=lambda x: x["created_at"], reverse=True)
    
    # 分页
    page_tasks = completed_tasks[offset:offset + limit]
    
    # 构建历史记录
    history = []
    for task in page_tasks:
        task_id = task["task_id"]
        results = recommendations.get(task_id, [])
        history.append({
            "task_id": task_id,
            "created_at": task["created_at"],
            "updated_at": task["updated_at"],
            "stock_pool_size": len(task["request"]["stock_pool"]),
            "top_n": task["request"]["top_n"],
            "recommendation_count": len(results),
            "factors": task["request"].get("factors", FACTOR_WEIGHTS)
        })
    
    return history


# 辅助函数
def get_factor_description(factor_name: str) -> str:
    """获取因子描述"""
    descriptions = {
        "收益因子": "衡量股票的历史收益率表现",
        "稳定因子": "衡量股票价格的稳定性（波动率的负值）",
        "活跃因子": "衡量股票的交易活跃度（成交量和涨跌幅的综合）",
        "质量因子": "衡量股票的投资质量（胜率、夏普率、最大回撤的综合）"
    }
    return descriptions.get(factor_name, "未知因子")


async def run_recommend_algorithm(task_id: str, request: RecommendRequest):
    """运行推荐算法"""
    try:
        # 更新任务状态
        tasks[task_id]["status"] = "running"
        tasks[task_id]["updated_at"] = datetime.now()
        
        # 在实际应用中，这里应该从数据库或缓存中获取策略回测结果
        # 这里使用模拟数据
        mock_results = generate_mock_results(request.stock_pool)
        
        # 更新因子统计信息
        if request.factors:
            # 使用自定义因子权重
            with temp_factor_weights(request.factors):
                factor_model.update_stats(request.stock_pool, mock_results)
                scores = calculate_stock_scores(request.stock_pool, mock_results, request.top_n)
        else:
            # 使用默认因子权重
            factor_model.update_stats(request.stock_pool, mock_results)
            scores = calculate_stock_scores(request.stock_pool, mock_results, request.top_n)
        
        # 构建推荐结果
        recommend_results = []
        for i, (stock_code, score, factor_scores) in enumerate(scores, 1):
            recommend_results.append({
                "task_id": task_id,
                "stock_code": stock_code,
                "ranking": i,
                "score": score,
                "trading_date": datetime.now(),
                "factor_scores": factor_scores,
                "description": f"推荐排名第{i}，综合得分{score:.2f}"
            })
        
        # 存储结果
        recommendations[task_id] = recommend_results
        
        # 更新任务状态为完成
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["updated_at"] = datetime.now()
        
        logger.info(f"推荐任务 {task_id} 完成，推荐了 {len(recommend_results)} 只股票")
        
    except Exception as e:
        logger.error(f"运行推荐算法失败 {task_id}: {str(e)}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["updated_at"] = datetime.now()
        tasks[task_id]["error"] = str(e)


def generate_mock_results(stock_pool: List[str]) -> List[Dict]:
    """生成模拟回测结果"""
    import random
    results = []
    
    # 模拟几个策略的回测结果
    for _ in range(3):
        strategy_result = {"stocks": {}}
        
        for stock in stock_pool:
            # 生成随机的回测数据
            strategy_result["stocks"][stock] = {
                "total_return": random.uniform(-0.2, 0.5),
                "volatility": random.uniform(0.1, 0.5),
                "sharpe_ratio": random.uniform(-1, 3),
                "max_drawdown": random.uniform(0.1, 0.4),
                "win_rate": random.uniform(0.3, 0.7),
                "close_prices": [random.uniform(10, 100) for _ in range(20)],
                "volume": [random.uniform(1000, 10000) for _ in range(20)],
                "daily_returns": [random.uniform(-0.05, 0.05) for _ in range(19)],
                "price_changes": [random.uniform(-0.05, 0.05) for _ in range(19)]
            }
        
        results.append(strategy_result)
    
    return results


def calculate_stock_scores(stock_pool: List[str], results: List[Dict], top_n: int) -> List[tuple]:
    """计算股票得分并排序"""
    scores = []
    
    for stock in stock_pool:
        # 计算综合评分
        total_score = factor_model.score(stock, results)
        # 获取各因子得分
        factor_scores = factor_model.get_factor_scores(stock, results)
        scores.append((stock, total_score, factor_scores))
    
    # 按得分降序排序
    scores.sort(key=lambda x: x[1], reverse=True)
    
    # 返回前N个
    return scores[:top_n]


class temp_factor_weights:
    """临时修改因子权重的上下文管理器"""
    def __init__(self, weights: Dict[str, float]):
        self.weights = weights
        self.original_weights = {}
    
    def __enter__(self):
        # 保存原始权重
        for factor in self.weights:
            if factor in FACTOR_WEIGHTS:
                self.original_weights[factor] = FACTOR_WEIGHTS[factor]
                FACTOR_WEIGHTS[factor] = self.weights[factor]
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复原始权重
        for factor, weight in self.original_weights.items():
            FACTOR_WEIGHTS[factor] = weight
