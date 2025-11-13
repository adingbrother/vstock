import uuid
import asyncio
import time
import enum
import traceback
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic
from abc import ABC, abstractmethod
import logging
from loguru import logger
from quant_web.core.task_manager import (
    BaseTask, TaskResult, register_task, TaskPriority,
    global_task_manager
)


@register_task("simulated_download")
class SimulatedDownloadTask(BaseTask):
    """模拟下载任务类"""
    
    def __init__(self, task_id: str = None, stock_list: list = None):
        super().__init__(task_id=task_id, priority=TaskPriority.MEDIUM)
        self.stock_list = stock_list or []
        self.queue = None
    
    async def execute_async(self, queue: asyncio.Queue) -> TaskResult:
        """异步执行模拟下载任务"""
        self.queue = queue
        self.start()
        
        total = len(self.stock_list)
        logger.info(f"Starting simulation download task {self.task_id} for {total} stocks")
        
        try:
            for i, s in enumerate(self.stock_list, start=1):
                # 模拟工作
                await asyncio.sleep(1 + random.random() * 0.5)
                
                # 更新进度
                progress = i / total
                self.update_progress(progress)
                
                # 发送结构化的进度消息
                msg = {
                    "type": "progress", 
                    "task_id": self.task_id, 
                    "percent": int(progress * 100), 
                    "message": f"{s} 已下载",
                    "progress": self.progress,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await queue.put(msg)
                logger.debug(f"Task {self.task_id} progress: {int(progress * 100)}% - {s}")
            
            # 完成任务
            await asyncio.sleep(0.2)
            await queue.put({
                "type": "done", 
                "task_id": self.task_id, 
                "message": "下载完成",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            result = TaskResult(success=True, data={"status": "done", "task_id": self.task_id})
            self.complete(result)
            logger.info(f"Simulation download task {self.task_id} completed successfully")
            return result
            
        except Exception as e:
            error_msg = str(e)
            error_stack = traceback.format_exc()
            logger.error(f"Error in simulation download task {self.task_id}: {error_msg}\n{error_stack}")
            
            await queue.put({
                "type": "error", 
                "task_id": self.task_id, 
                "error_code": "DOWNLOAD_ERROR",
                "message": f"下载失败: {error_msg}",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            error_result = TaskResult(success=False, error_message=error_msg)
            self.complete(error_result)
            return error_result


@register_task("backtest")
class BacktestTask(BaseTask):
    """回测任务类"""
    
    def __init__(self, task_id: str = None, strategy_config: dict = None, 
                 stock_pool: list = None, start_date: datetime = None, 
                 end_date: datetime = None):
        super().__init__(task_id=task_id, priority=TaskPriority.HIGH)
        self.strategy_config = strategy_config or {}
        self.stock_pool = stock_pool or []
        self.start_date = start_date or (datetime.now() - timedelta(days=365))
        self.end_date = end_date or datetime.now()
        self.queue = None
    
    def execute(self) -> TaskResult:
        """实现BaseTask的抽象方法execute
        
        在同步环境中执行回测任务
        """
        self.start()
        
        try:
            # 导入需要的模块
            from quant_web.core.be.trading_engine import TradingEngine
            from quant_web.core.be.data_feed import DataFeed
            
            # 创建交易引擎
            engine = TradingEngine()
            engine.initialize()
            
            # 创建数据馈送
            data_feed = DataFeed()
            
            # 加载历史数据
            self.update_progress(0.2)
            success = data_feed.load_historical_data(self.stock_pool, self.start_date, self.end_date)
            
            if not success:
                raise Exception("加载历史数据失败")
            
            # 加载数据到交易引擎
            engine.load_data_feed(data_feed)
            
            # 添加策略
            self.update_progress(0.5)
            if self.strategy_config:
                strategy_name = self.strategy_config.get("name", "moving_average")
                strategy_id = f"{strategy_name}_{self.task_id[:8]}"
                parameters = self.strategy_config.get("parameters", {})
                
                engine.add_strategy(
                    strategy_name=strategy_name,
                    strategy_id=strategy_id,
                    parameters=parameters
                )
            
            # 执行回测
            self.update_progress(0.6)
            backtest_result = engine.execute_backtest(self.start_date, self.end_date)
            
            # 准备结果
            self.update_progress(0.9)
            result_data = {
                "status": "done",
                "task_id": self.task_id,
                "backtest_result": backtest_result,
                "strategy_config": self.strategy_config,
                "time_range": {
                    "start_date": self.start_date.isoformat(),
                    "end_date": self.end_date.isoformat()
                },
                "stock_count": len(self.stock_pool)
            }
            
            result = TaskResult(success=True, data=result_data)
            self.complete(result)
            logger.info(f"Backtest task {self.task_id} done")
            return result
            
        except Exception as e:
            error_msg = str(e)
            error_stack = traceback.format_exc()
            logger.error(f"Error in backtest task {self.task_id}: {error_msg}\n{error_stack}")
            
            error_result = TaskResult(success=False, error_message=error_msg)
            self.complete(error_result)
            return error_result
    
    async def execute_async(self, queue: asyncio.Queue) -> TaskResult:
        """异步执行回测任务"""
        self.queue = queue
        self.start()
        
        logger.info(f"Starting backtest task {self.task_id} with strategy: {self.strategy_config.get('name', 'default')}")
        logger.info(f"Backtest parameters: stocks={len(self.stock_pool)}, start={self.start_date}, end={self.end_date}")
        
        try:
            # 导入需要的模块
            from quant_web.core.be.trading_engine import TradingEngine
            from quant_web.core.be.data_feed import DataFeed
            from quant_web.core.exceptions import DataError, StrategyError, BacktestError
            
            # 发送结构化的开始消息
            await queue.put({
                "type": "progress", 
                "task_id": self.task_id, 
                "percent": 5,
                "message": "初始化回测引擎...",
                "progress": 0.05,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.update_progress(0.05)
            
            # 创建交易引擎
            engine = TradingEngine()
            engine.initialize()
            logger.debug(f"Trading engine initialized for task {self.task_id}")
            
            # 发送进度消息
            await queue.put({
                "type": "progress", 
                "task_id": self.task_id, 
                "percent": 10,
                "message": "创建数据馈送...",
                "progress": 0.1,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.update_progress(0.1)
            
            # 创建数据馈送
            data_feed = DataFeed()
            
            # 加载历史数据
            await queue.put({
                "type": "progress", 
                "task_id": self.task_id, 
                "percent": 20,
                "message": "加载历史数据...",
                "progress": 0.2,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.update_progress(0.2)
            
            # 加载数据（这里使用同步调用但在异步环境中）
            # 实际实现中可能需要使用asyncio.to_thread来避免阻塞
            await asyncio.sleep(0.5)  # 短暂暂停以避免阻塞
            
            try:
                success = data_feed.load_historical_data(self.stock_pool, self.start_date, self.end_date)
                if not success:
                    raise DataError("加载历史数据失败", details={"stock_count": len(self.stock_pool)})
            except DataError:
                raise
            except Exception as e:
                raise DataError(f"数据加载过程中发生错误: {str(e)}", details={"stock_count": len(self.stock_pool)})
            
            # 发送进度消息
            await queue.put({
                "type": "progress", 
                "task_id": self.task_id, 
                "percent": 40,
                "message": "数据加载完成，准备回测...",
                "progress": 0.4,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.update_progress(0.4)
            
            # 加载数据到交易引擎
            engine.load_data_feed(data_feed)
            logger.debug(f"Data feed loaded for task {self.task_id}")
            
            # 添加策略
            await queue.put({
                "type": "progress", 
                "task_id": self.task_id, 
                "percent": 50,
                "message": "添加交易策略...",
                "progress": 0.5,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.update_progress(0.5)
            
            # 如果提供了策略配置，则添加策略
            if self.strategy_config:
                strategy_name = self.strategy_config.get("name", "moving_average")
                strategy_id = f"{strategy_name}_{self.task_id[:8]}"
                parameters = self.strategy_config.get("parameters", {})
                
                try:
                    engine.add_strategy(
                        strategy_name=strategy_name,
                        strategy_id=strategy_id,
                        parameters=parameters
                    )
                    logger.info(f"Strategy {strategy_name} added to task {self.task_id}")
                except Exception as e:
                    raise StrategyError(f"策略添加失败: {str(e)}", strategy_name=strategy_name)
            
            # 执行回测
            await queue.put({
                "type": "progress", 
                "task_id": self.task_id, 
                "percent": 60,
                "message": "开始回测计算...",
                "progress": 0.6,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.update_progress(0.6)
            
            # 执行回测（同样，在实际实现中可能需要使用asyncio.to_thread）
            try:
                await asyncio.sleep(0.5)
                backtest_result = engine.execute_backtest(self.start_date, self.end_date)
                logger.debug(f"Backtest execution completed for task {self.task_id}")
            except Exception as e:
                raise BacktestError(f"回测执行失败: {str(e)}")
            
            # 更新进度
            await queue.put({
                "type": "progress", 
                "task_id": self.task_id, 
                "percent": 90,
                "message": "回测计算完成，正在处理结果...",
                "progress": 0.9,
                "timestamp": datetime.utcnow().isoformat()
            })
            self.update_progress(0.9)
            
            # 准备结果
            result_data = {
                "status": "done",
                "task_id": self.task_id,
                "backtest_result": backtest_result,
                "strategy_config": self.strategy_config,
                "time_range": {
                    "start_date": self.start_date.isoformat(),
                    "end_date": self.end_date.isoformat()
                },
                "stock_count": len(self.stock_pool)
            }
            
            # 完成任务
            await asyncio.sleep(0.2)
            await queue.put({
                "type": "done", 
                "task_id": self.task_id, 
                "message": "回测完成",
                "data": {"backtest_id": self.task_id},
                "timestamp": datetime.utcnow().isoformat()
            })
            
            result = TaskResult(success=True, data=result_data)
            self.complete(result)
            logger.info(f"Backtest task {self.task_id} completed successfully")
            return result
            
        except DataError as e:
            error_msg = str(e)
            error_stack = traceback.format_exc()
            logger.error(f"Data error in backtest task {self.task_id}: {error_msg}\n{error_stack}")
            
            await queue.put({
                "type": "error", 
                "task_id": self.task_id, 
                "error_code": "DATA_ERROR",
                "message": f"数据错误: {error_msg}",
                "details": e.details or {},
                "timestamp": datetime.utcnow().isoformat()
            })
            
            error_result = TaskResult(success=False, error_message=error_msg)
            self.complete(error_result)
            return error_result
        
        except StrategyError as e:
            error_msg = str(e)
            error_stack = traceback.format_exc()
            logger.error(f"Strategy error in backtest task {self.task_id}: {error_msg}\n{error_stack}")
            
            await queue.put({
                "type": "error", 
                "task_id": self.task_id, 
                "error_code": "STRATEGY_ERROR",
                "message": f"策略错误: {error_msg}",
                "details": e.details or {},
                "timestamp": datetime.utcnow().isoformat()
            })
            
            error_result = TaskResult(success=False, error_message=error_msg)
            self.complete(error_result)
            return error_result
            
        except BacktestError as e:
            error_msg = str(e)
            error_stack = traceback.format_exc()
            logger.error(f"Backtest error in backtest task {self.task_id}: {error_msg}\n{error_stack}")
            
            await queue.put({
                "type": "error", 
                "task_id": self.task_id, 
                "error_code": "BACKTEST_ERROR",
                "message": f"回测错误: {error_msg}",
                "details": e.details or {},
                "timestamp": datetime.utcnow().isoformat()
            })
            
            error_result = TaskResult(success=False, error_message=error_msg)
            self.complete(error_result)
            return error_result
            
        except Exception as e:
            error_msg = str(e)
            error_stack = traceback.format_exc()
            logger.error(f"Unexpected error in backtest task {self.task_id}: {error_msg}\n{error_stack}")
            
            await queue.put({
                "type": "error", 
                "task_id": self.task_id, 
                "error_code": "INTERNAL_ERROR",
                "message": f"回测失败: {error_msg}",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            error_result = TaskResult(success=False, error_message=error_msg)
            self.complete(error_result)
            return error_result


async def start_download_simulation(task_id: str, stock_list: list[str], queue: asyncio.Queue):
    """模拟下载任务入口，使用SimulatedDownloadTask类

    This is a local in-memory simulation used for the skeleton. Real implementation should
    enqueue a Celery task and publish progress to Redis Pub/Sub for cross-process delivery.
    """
    # 创建任务实例
    task = SimulatedDownloadTask(task_id=task_id, stock_list=stock_list)
    
    # 添加到全局任务管理器
    global_task_manager.add_task(task)
    
    # 执行异步任务
    await task.execute_async(queue)


async def start_backtest_task(task_id: str, strategy_config: dict, stock_pool: list, 
                             start_date: datetime, end_date: datetime, 
                             queue: asyncio.Queue):
    """回测任务入口，使用BacktestTask类
    
    Args:
        task_id: 任务ID
        strategy_config: 策略配置，包含name和parameters
        stock_pool: 股票池列表
        start_date: 回测开始日期
        end_date: 回测结束日期
        queue: 消息队列，用于发送进度和结果
    """
    # 创建任务实例
    task = BacktestTask(
        task_id=task_id,
        strategy_config=strategy_config,
        stock_pool=stock_pool,
        start_date=start_date,
        end_date=end_date
    )
    
    # 添加到全局任务管理器
    global_task_manager.add_task(task)
    
    # 执行异步任务
    await task.execute_async(queue)
