from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from loguru import logger

from quant_web.core.be.strategy import StrategyFactory
from quant_web.core.exceptions import StrategyError

router = APIRouter()


class StrategyInfo(BaseModel):
    """策略信息模型"""
    name: str = Field(..., description="策略名称")
    description: str = Field(..., description="策略描述")
    default_parameters: Dict = Field(default_factory=dict, description="默认参数")


class StrategyCreateRequest(BaseModel):
    """创建策略实例请求模型"""
    strategy_name: str = Field(..., description="策略名称")
    strategy_id: str = Field(..., description="策略实例ID")
    parameters: Optional[Dict] = Field(default_factory=dict, description="策略参数")


class StrategyUpdateRequest(BaseModel):
    """更新策略参数请求模型"""
    parameters: Dict = Field(..., description="要更新的策略参数")


# 全局策略实例存储
_strategy_instances: Dict[str, Dict] = {}


@router.get("/strategies/list", response_model=List[str])
async def get_available_strategies():
    """获取所有可用的策略名称"""
    try:
        strategies = StrategyFactory.get_available_strategies()
        logger.info(f"Retrieved available strategies: {strategies}")
        return strategies
    except Exception as e:
        logger.error(f"Failed to retrieve strategies: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": 50001, "message": "获取策略列表失败"})


@router.get("/strategies/info/{strategy_name}", response_model=StrategyInfo)
async def get_strategy_info(strategy_name: str):
    """获取特定策略的详细信息"""
    try:
        # 创建临时策略实例以获取信息
        temp_strategy = StrategyFactory.create(strategy_name, "temp_id")
        
        info = StrategyInfo(
            name=strategy_name,
            description=temp_strategy.description,
            default_parameters=temp_strategy.get_parameters()
        )
        
        logger.info(f"Retrieved info for strategy: {strategy_name}")
        return info
    except ValueError as e:
        logger.error(f"Strategy not found: {strategy_name}")
        raise HTTPException(status_code=404, detail={"code": 40401, "message": "策略不存在"})
    except Exception as e:
        logger.error(f"Failed to get strategy info: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": 50002, "message": "获取策略信息失败"})


@router.post("/strategies/create", status_code=201)
async def create_strategy(req: StrategyCreateRequest):
    """创建策略实例"""
    try:
        # 检查策略ID是否已存在
        if req.strategy_id in _strategy_instances:
            raise HTTPException(status_code=400, detail={"code": 40001, "message": "策略实例ID已存在"})
        
        # 创建策略实例
        strategy = StrategyFactory.create(req.strategy_name, req.strategy_id)
        
        # 设置参数
        if req.parameters:
            strategy.set_parameters(req.parameters)
        
        # 保存策略实例
        _strategy_instances[req.strategy_id] = {
            "strategy": strategy,
            "name": req.strategy_name,
            "created_at": "2024-01-01T00:00:00Z"  # 在实际应用中使用当前时间
        }
        
        logger.info(f"Created strategy instance: {req.strategy_id} of type {req.strategy_name}")
        
        return {
            "strategy_id": req.strategy_id,
            "strategy_name": req.strategy_name,
            "parameters": strategy.get_parameters(),
            "message": "策略实例创建成功"
        }
    except ValueError as e:
        logger.error(f"Strategy creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail={"code": 40002, "message": f"无效的策略名称: {str(e)}"})
    except Exception as e:
        logger.error(f"Failed to create strategy: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": 50003, "message": "创建策略实例失败"})


@router.get("/strategies/instances/{strategy_id}")
async def get_strategy_instance(strategy_id: str):
    """获取策略实例详情"""
    try:
        instance = _strategy_instances.get(strategy_id)
        if not instance:
            raise HTTPException(status_code=404, detail={"code": 40402, "message": "策略实例不存在"})
        
        strategy = instance["strategy"]
        
        return {
            "strategy_id": strategy_id,
            "strategy_name": instance["name"],
            "parameters": strategy.get_parameters(),
            "description": strategy.description,
            "created_at": instance["created_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get strategy instance: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": 50004, "message": "获取策略实例失败"})


@router.put("/strategies/instances/{strategy_id}")
async def update_strategy_parameters(strategy_id: str, req: StrategyUpdateRequest):
    """更新策略参数"""
    try:
        instance = _strategy_instances.get(strategy_id)
        if not instance:
            raise HTTPException(status_code=404, detail={"code": 40402, "message": "策略实例不存在"})
        
        # 更新参数
        strategy = instance["strategy"]
        strategy.set_parameters(req.parameters)
        
        logger.info(f"Updated parameters for strategy instance: {strategy_id}")
        
        return {
            "strategy_id": strategy_id,
            "strategy_name": instance["name"],
            "parameters": strategy.get_parameters(),
            "message": "策略参数更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update strategy parameters: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": 50005, "message": "更新策略参数失败"})


@router.delete("/strategies/instances/{strategy_id}")
async def delete_strategy_instance(strategy_id: str):
    """删除策略实例"""
    try:
        if strategy_id not in _strategy_instances:
            raise HTTPException(status_code=404, detail={"code": 40402, "message": "策略实例不存在"})
        
        # 删除策略实例
        del _strategy_instances[strategy_id]
        
        logger.info(f"Deleted strategy instance: {strategy_id}")
        
        return {
            "strategy_id": strategy_id,
            "message": "策略实例删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete strategy instance: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": 50006, "message": "删除策略实例失败"})


@router.get("/strategies/instances")
async def list_strategy_instances():
    """获取所有策略实例列表"""
    try:
        instances = []
        for strategy_id, instance_data in _strategy_instances.items():
            strategy = instance_data["strategy"]
            instances.append({
                "strategy_id": strategy_id,
                "strategy_name": instance_data["name"],
                "description": strategy.description,
                "parameters": strategy.get_parameters(),
                "created_at": instance_data["created_at"]
            })
        
        logger.info(f"Retrieved {len(instances)} strategy instances")
        return instances
    except Exception as e:
        logger.error(f"Failed to list strategy instances: {str(e)}")
        raise HTTPException(status_code=500, detail={"code": 50007, "message": "获取策略实例列表失败"})
