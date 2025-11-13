import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

from quant_web.core.be.strategy import Strategy, StrategyFactory
from quant_web.core.const import MIN_TRADE_QUANTITY


@StrategyFactory.register("moving_average")
class MovingAverageStrategy(Strategy):
    """移动平均线策略"""
    
    def __init__(self, strategy_id: str):
        super().__init__(strategy_id)
        self.description = "基于短期和长期移动平均线交叉的交易策略"
        # 默认参数
        self.set_parameters({
            'short_window': 20,
            'long_window': 50,
            'position_ratio': 0.1  # 每次交易使用总资产的比例
        })
    
    def initialize(self, context: Dict) -> None:
        """初始化策略"""
        # 从上下文获取必要信息
        self.portfolio = context.get('portfolio')
        self.initial_cash = context.get('initial_cash', 1000000)
    
    def on_data(self, date: datetime, data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """生成交易信号"""
        signals = []
        
        for ts_code, df in data.items():
            # 确保有足够的数据计算移动平均线
            if len(df) < self.parameters['long_window']:
                continue
            
            # 计算移动平均线
            df['short_ma'] = df['close'].rolling(window=self.parameters['short_window']).mean()
            df['long_ma'] = df['close'].rolling(window=self.parameters['long_window']).mean()
            
            # 检查是否有足够的历史数据来判断交叉
            if len(df) >= self.parameters['long_window'] + 1:
                # 金叉信号（短期均线上穿长期均线）
                if (df['short_ma'].iloc[-2] < df['long_ma'].iloc[-2] and 
                    df['short_ma'].iloc[-1] > df['long_ma'].iloc[-1]):
                    
                    # 计算买入数量
                    available_cash = self.portfolio.cash if self.portfolio else self.initial_cash
                    buy_value = available_cash * self.parameters['position_ratio']
                    price = df['close'].iloc[-1]
                    quantity = max(int(buy_value / price), MIN_TRADE_QUANTITY)
                    
                    signals.append({
                        'ts_code': ts_code,
                        'side': 'buy',
                        'quantity': quantity,
                        'price': price,
                        'signal_type': 'golden_cross'
                    })
                
                # 死叉信号（短期均线下穿长期均线）
                elif (df['short_ma'].iloc[-2] > df['long_ma'].iloc[-2] and 
                      df['short_ma'].iloc[-1] < df['long_ma'].iloc[-1]):
                    
                    # 如果持有该股票，则卖出全部
                    if self.portfolio and ts_code in self.portfolio.positions:
                        quantity = self.portfolio.positions[ts_code]
                        signals.append({
                            'ts_code': ts_code,
                            'side': 'sell',
                            'quantity': quantity,
                            'price': df['close'].iloc[-1],
                            'signal_type': 'death_cross'
                        })
        
        return signals


@StrategyFactory.register("rsi_strategy")
class RSIStrategy(Strategy):
    """RSI策略"""
    
    def __init__(self, strategy_id: str):
        super().__init__(strategy_id)
        self.description = "基于相对强弱指标(RSI)的超买超卖策略"
        # 默认参数
        self.set_parameters({
            'rsi_window': 14,
            'oversold_threshold': 30,
            'overbought_threshold': 70,
            'position_ratio': 0.1
        })
    
    def initialize(self, context: Dict) -> None:
        """初始化策略"""
        self.portfolio = context.get('portfolio')
        self.initial_cash = context.get('initial_cash', 1000000)
    
    def _calculate_rsi(self, data: pd.Series, window: int) -> pd.Series:
        """计算RSI指标"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def on_data(self, date: datetime, data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """生成交易信号"""
        signals = []
        
        for ts_code, df in data.items():
            # 确保有足够的数据
            if len(df) < self.parameters['rsi_window']:
                continue
            
            # 计算RSI
            df['rsi'] = self._calculate_rsi(df['close'], self.parameters['rsi_window'])
            
            # 获取最新的RSI值
            current_rsi = df['rsi'].iloc[-1]
            price = df['close'].iloc[-1]
            
            # 超卖信号（RSI低于阈值）
            if current_rsi < self.parameters['oversold_threshold']:
                available_cash = self.portfolio.cash if self.portfolio else self.initial_cash
                buy_value = available_cash * self.parameters['position_ratio']
                quantity = max(int(buy_value / price), MIN_TRADE_QUANTITY)
                
                signals.append({
                    'ts_code': ts_code,
                    'side': 'buy',
                    'quantity': quantity,
                    'price': price,
                    'signal_type': 'oversold'
                })
            
            # 超买信号（RSI高于阈值）
            elif current_rsi > self.parameters['overbought_threshold']:
                if self.portfolio and ts_code in self.portfolio.positions:
                    quantity = self.portfolio.positions[ts_code]
                    signals.append({
                        'ts_code': ts_code,
                        'side': 'sell',
                        'quantity': quantity,
                        'price': price,
                        'signal_type': 'overbought'
                    })
        
        return signals


@StrategyFactory.register("momentum")
class MomentumStrategy(Strategy):
    """动量策略"""
    
    def __init__(self, strategy_id: str):
        super().__init__(strategy_id)
        self.description = "基于价格动量的交易策略"
        # 默认参数
        self.set_parameters({
            'lookback_period': 20,  # 回看周期
            'top_n': 3,  # 选择动量最强的N只股票
            'rebalance_days': 5  # 调仓周期（天）
        })
        self.last_rebalance_date = None
    
    def initialize(self, context: Dict) -> None:
        """初始化策略"""
        self.portfolio = context.get('portfolio')
        self.initial_cash = context.get('initial_cash', 1000000)
    
    def on_data(self, date: datetime, data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """生成交易信号"""
        # 检查是否需要调仓
        if self.last_rebalance_date is None or \
           (date - self.last_rebalance_date).days >= self.parameters['rebalance_days']:
            
            self.last_rebalance_date = date
            signals = []
            momentum_scores = {}
            
            # 计算每只股票的动量
            for ts_code, df in data.items():
                if len(df) >= self.parameters['lookback_period']:
                    # 计算收益率作为动量指标
                    start_price = df['close'].iloc[-self.parameters['lookback_period']]
                    end_price = df['close'].iloc[-1]
                    momentum = (end_price / start_price) - 1
                    momentum_scores[ts_code] = momentum
            
            # 选择动量最强的股票
            sorted_stocks = sorted(momentum_scores.items(), key=lambda x: x[1], reverse=True)
            top_stocks = [ts_code for ts_code, _ in sorted_stocks[:self.parameters['top_n']]]
            
            # 获取当前持仓
            current_positions = set(self.portfolio.positions.keys()) if self.portfolio else set()
            target_stocks = set(top_stocks)
            
            # 卖出不在目标列表中的股票
            for ts_code in current_positions - target_stocks:
                if self.portfolio and ts_code in self.portfolio.positions:
                    quantity = self.portfolio.positions[ts_code]
                    price = data[ts_code]['close'].iloc[-1]
                    signals.append({
                        'ts_code': ts_code,
                        'side': 'sell',
                        'quantity': quantity,
                        'price': price,
                        'signal_type': 'exit'
                    })
            
            # 计算可用资金
            total_value = self.portfolio.get_total_value({}) if self.portfolio else self.initial_cash
            available_cash = self.portfolio.cash if self.portfolio else self.initial_cash
            
            # 买入目标股票
            for ts_code in target_stocks - current_positions:
                if ts_code in data:
                    # 平均分配资金
                    allocation = total_value / self.parameters['top_n']
                    price = data[ts_code]['close'].iloc[-1]
                    quantity = max(int(allocation / price), MIN_TRADE_QUANTITY)
                    
                    signals.append({
                        'ts_code': ts_code,
                        'side': 'buy',
                        'quantity': quantity,
                        'price': price,
                        'signal_type': 'enter'
                    })
            
            return signals
        
        return []
