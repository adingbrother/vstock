from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
from loguru import logger


class Strategy(ABC):
    """策略抽象基类"""
    
    def __init__(self, strategy_id: str):
        self.strategy_id = strategy_id
        self.name = self.__class__.__name__
        self.description = ""
        self.parameters = {}
        self.signals = []
        logger.info(f"Initialized strategy: {self.name} (ID: {self.strategy_id})")
    
    @abstractmethod
    def initialize(self, context: Dict) -> None:
        """初始化策略"""
        pass
    
    @abstractmethod
    def on_data(self, date: datetime, data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """处理数据并生成交易信号
        
        Args:
            date: 当前日期
            data: 可用的价格数据，格式为 {ts_code: dataframe}
            
        Returns:
            交易信号列表，每个信号格式为：
            {
                'ts_code': '股票代码',
                'side': 'buy'或'sell',
                'quantity': 数量,
                'price': 价格（可选）,
                'signal_type': '信号类型'
            }
        """
        pass
    
    def set_parameters(self, parameters: Dict) -> None:
        """设置策略参数"""
        self.parameters.update(parameters)
        logger.debug(f"Set parameters for {self.name}: {parameters}")
    
    def get_parameters(self) -> Dict:
        """获取策略参数"""
        return self.parameters
    
    def on_order_filled(self, order: Dict) -> None:
        """订单成交回调"""
        logger.info(f"Order filled: {order}")
    
    def on_order_cancelled(self, order: Dict) -> None:
        """订单取消回调"""
        logger.info(f"Order cancelled: {order}")
    
    def record(self, key: str, value: float) -> None:
        """记录指标"""
        self.signals.append({
            'timestamp': datetime.now(),
            'key': key,
            'value': value
        })
    
    def get_signals(self) -> List[Dict]:
        """获取信号历史"""
        return self.signals


class StrategyFactory:
    """策略工厂类"""
    
    _strategies = {}
    
    @classmethod
    def register(cls, name: str) -> callable:
        """注册策略"""
        def decorator(strategy_class):
            cls._strategies[name] = strategy_class
            return strategy_class
        return decorator
    
    @classmethod
    def create(cls, name: str, strategy_id: str, **kwargs) -> Strategy:
        """创建策略实例"""
        if name not in cls._strategies:
            raise ValueError(f"Strategy {name} not found")
        
        strategy_class = cls._strategies[name]
        strategy = strategy_class(strategy_id, **kwargs)
        return strategy
    
    @classmethod
    def get_available_strategies(cls) -> List[str]:
        """获取所有可用的策略名称"""
        return list(cls._strategies.keys())


class StrategyContext:
    """策略上下文类，提供策略运行环境"""
    
    def __init__(self):
        self.portfolio = None
        self.initial_cash = 0
        self.start_date = None
        self.end_date = None
        self.stock_pool = []
        self.data_feed = None
        self.position_manager = None
    
    def update(self, **kwargs) -> None:
        """更新上下文信息"""
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def get(self, key, default=None):
        """获取上下文中的属性值"""
        if hasattr(self, key):
            return getattr(self, key)
        return default
