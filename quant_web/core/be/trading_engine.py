from typing import Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
from loguru import logger

from quant_web.core.be.strategy import Strategy, StrategyFactory, StrategyContext
from quant_web.core.be.portfolio import Portfolio
from quant_web.core.be.order import Order, OrderStatus
from quant_web.core.be.data_feed import DataFeed
from quant_web.core.const import MIN_TRADE_QUANTITY

# 导入策略模块，确保策略被注册
from quant_web.core.be.strategies import *


class TradingEngine:
    """交易引擎，负责执行策略、处理订单和管理投资组合"""
    
    def __init__(self):
        self.strategies: Dict[str, Strategy] = {}
        self.portfolio: Optional[Portfolio] = None
        self.data_feed: Optional[DataFeed] = None
        self.open_orders: List[Order] = []
        self.order_history: List[Order] = []
        self.performance_metrics: Dict = {}
        self.current_date: Optional[datetime] = None
    
    def initialize(self, initial_cash: float = 1000000.0) -> None:
        """初始化交易引擎"""
        self.portfolio = Portfolio(initial_cash)
        logger.info(f"Trading engine initialized with cash: {initial_cash}")
    
    def load_data_feed(self, data_feed: DataFeed) -> None:
        """加载数据馈送"""
        self.data_feed = data_feed
        logger.info(f"Data feed loaded with {len(data_feed.get_available_stocks())} stocks")
    
    def add_strategy(self, strategy_name: str, strategy_id: str, parameters: Optional[Dict] = None) -> Strategy:
        """添加策略"""
        try:
            # 使用策略工厂创建策略实例
            strategy = StrategyFactory.create(strategy_name, strategy_id)
            
            # 设置策略参数
            if parameters:
                strategy.set_parameters(parameters)
            
            self.strategies[strategy_id] = strategy
            logger.info(f"Added strategy: {strategy_name} (ID: {strategy_id})")
            
            # 初始化策略
            context = StrategyContext()
            context.portfolio = self.portfolio
            context.initial_cash = self.portfolio.initial_cash
            context.stock_pool = self.data_feed.get_available_stocks() if self.data_feed else []
            context.data_feed = self.data_feed
            
            strategy.initialize(context)
            return strategy
        except Exception as e:
            logger.error(f"Failed to add strategy {strategy_name}: {str(e)}")
            raise
    
    def remove_strategy(self, strategy_id: str) -> None:
        """移除策略"""
        if strategy_id in self.strategies:
            del self.strategies[strategy_id]
            logger.info(f"Removed strategy: {strategy_id}")
        else:
            logger.warning(f"Strategy {strategy_id} not found")
    
    def execute_backtest(self, start_date: datetime, end_date: datetime) -> Dict:
        """执行回测"""
        if not self.data_feed:
            raise ValueError("Data feed not loaded")
        
        if not self.strategies:
            raise ValueError("No strategies added")
        
        logger.info(f"Starting backtest from {start_date} to {end_date}")
        
        # 重置状态
        self.portfolio.reset()
        self.open_orders = []
        self.order_history = []
        
        # 获取回测期间的所有日期
        trading_dates = self.data_feed.get_trading_dates(start_date, end_date)
        
        # 用于记录每日净值
        daily_equity = []
        
        for date in trading_dates:
            self.current_date = date
            
            # 处理未完成订单
            self._process_orders(date)
            
            # 获取当日数据
            market_data = self.data_feed.get_data_for_date(date)
            
            if not market_data:
                continue
            
            # 执行所有策略
            for strategy_id, strategy in self.strategies.items():
                try:
                    signals = strategy.on_data(date, market_data)
                    self._process_signals(signals, date, strategy_id)
                except Exception as e:
                    logger.error(f"Error executing strategy {strategy_id}: {str(e)}")
            
            # 计算当日净值
            current_equity = self.portfolio.get_total_value(market_data)
            daily_equity.append({
                'date': date,
                'equity': current_equity
            })
        
        # 计算绩效指标
        self._calculate_performance_metrics(daily_equity)
        
        logger.info(f"Backtest completed. Final equity: {daily_equity[-1]['equity']}")
        
        return {
            'daily_equity': daily_equity,
            'performance_metrics': self.performance_metrics,
            'order_history': self.order_history
        }
    
    def _process_signals(self, signals: List[Dict], date: datetime, strategy_id: str) -> None:
        """处理交易信号，生成订单"""
        for signal in signals:
            ts_code = signal['ts_code']
            side = signal['side']
            quantity = signal['quantity']
            price = signal.get('price')
            signal_type = signal.get('signal_type', 'unknown')
            
            # 验证交易数量
            if quantity < MIN_TRADE_QUANTITY:
                logger.warning(f"Order quantity below minimum: {quantity}")
                continue
            
            # 创建订单
            order = Order(
                order_id=f"{date.strftime('%Y%m%d')}_{strategy_id}_{len(self.open_orders) + 1}",
                strategy_id=strategy_id,
                ts_code=ts_code,
                side=side,
                quantity=quantity,
                price=price,
                signal_type=signal_type,
                created_at=date
            )
            
            # 检查是否可以执行订单
            if side == 'buy':
                if not self.portfolio.can_buy(ts_code, quantity, price):
                    logger.warning(f"Insufficient cash for buy order: {ts_code} - {quantity} shares")
                    continue
            elif side == 'sell':
                if not self.portfolio.can_sell(ts_code, quantity):
                    logger.warning(f"Insufficient shares for sell order: {ts_code} - {quantity} shares")
                    continue
            
            # 添加到订单列表
            self.open_orders.append(order)
            logger.info(f"Created {side} order: {ts_code} - {quantity} shares at {price}")
    
    def _process_orders(self, date: datetime) -> None:
        """处理订单（模拟订单成交）"""
        orders_to_remove = []
        
        for order in self.open_orders:
            try:
                # 模拟订单成交
                order.fill(date, order.price)
                
                # 更新投资组合
                if order.side == 'buy':
                    self.portfolio.buy(order.ts_code, order.quantity, order.price)
                elif order.side == 'sell':
                    self.portfolio.sell(order.ts_code, order.quantity, order.price)
                
                # 通知策略订单成交
                if order.strategy_id in self.strategies:
                    self.strategies[order.strategy_id].on_order_filled(order.to_dict())
                
                orders_to_remove.append(order)
                self.order_history.append(order)
                
            except Exception as e:
                logger.error(f"Error processing order {order.order_id}: {str(e)}")
        
        # 移除已处理的订单
        for order in orders_to_remove:
            self.open_orders.remove(order)
    
    def _calculate_performance_metrics(self, daily_equity: List[Dict]) -> None:
        """计算绩效指标"""
        df = pd.DataFrame(daily_equity)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # 计算收益率
        df['returns'] = df['equity'].pct_change()
        
        # 累计收益
        df['cumulative_returns'] = (1 + df['returns']).cumprod()
        
        # 计算基本指标
        total_return = (df['equity'].iloc[-1] / df['equity'].iloc[0]) - 1
        annual_return = ((1 + total_return) ** (252 / len(df))) - 1
        
        # 计算风险指标
        daily_volatility = df['returns'].std()
        annual_volatility = daily_volatility * np.sqrt(252)
        
        # 计算最大回撤
        df['cumulative_max'] = df['equity'].cummax()
        df['drawdown'] = (df['equity'] - df['cumulative_max']) / df['cumulative_max']
        max_drawdown = df['drawdown'].min()
        
        # 计算夏普比率（假设无风险利率为3%）
        risk_free_rate = 0.03
        sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility != 0 else 0
        
        # 计算索提诺比率
        downside_returns = df['returns'][df['returns'] < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252)
        sortino_ratio = (annual_return - risk_free_rate) / downside_deviation if downside_deviation != 0 else 0
        
        self.performance_metrics = {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'trades_count': len(self.order_history),
            'win_rate': self._calculate_win_rate(),
            'profit_factor': self._calculate_profit_factor()
        }
    
    def _calculate_win_rate(self) -> float:
        """计算胜率"""
        profitable_trades = 0
        total_trades = len(self.order_history)
        
        if total_trades == 0:
            return 0
        
        # 简单的胜率计算（实际应该匹配买卖订单）
        for i in range(0, min(total_trades, total_trades - 1), 2):
            if i + 1 < total_trades:
                buy_order = self.order_history[i]
                sell_order = self.order_history[i + 1]
                if buy_order.ts_code == sell_order.ts_code and buy_order.side == 'buy' and sell_order.side == 'sell':
                    if sell_order.price > buy_order.price:
                        profitable_trades += 1
        
        return profitable_trades / (total_trades // 2) if total_trades >= 2 else 0
    
    def _calculate_profit_factor(self) -> float:
        """计算盈利因子"""
        total_profit = 0
        total_loss = 0
        
        # 简单的盈利因子计算
        for i in range(0, min(len(self.order_history), len(self.order_history) - 1), 2):
            if i + 1 < len(self.order_history):
                buy_order = self.order_history[i]
                sell_order = self.order_history[i + 1]
                if buy_order.ts_code == sell_order.ts_code and buy_order.side == 'buy' and sell_order.side == 'sell':
                    profit = (sell_order.price - buy_order.price) * sell_order.quantity
                    if profit > 0:
                        total_profit += profit
                    else:
                        total_loss += abs(profit)
        
        return total_profit / total_loss if total_loss != 0 else 0
    
    def get_portfolio_status(self) -> Dict:
        """获取投资组合当前状态"""
        return self.portfolio.to_dict() if self.portfolio else {}
    
    def get_open_orders(self) -> List[Dict]:
        """获取未完成订单"""
        return [order.to_dict() for order in self.open_orders]
    
    def get_order_history(self) -> List[Dict]:
        """获取订单历史"""
        return [order.to_dict() for order in self.order_history]
    
    def _get_available_strategies(self) -> List[str]:
        """获取可用策略列表"""
        return StrategyFactory.get_available_strategies()
