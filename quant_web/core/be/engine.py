import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
from loguru import logger

from quant_web.core.be.matcher import SimpleMatcher, Order, Bar
from quant_web.core.const import MAX_DD_THRESHOLD
from quant_web.core.exceptions import BacktestError


class Portfolio:
    """投资组合管理类"""
    
    def __init__(self, initial_cash: float):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, int] = {}  # 股票代码 -> 持仓数量
        self.position_prices: Dict[str, float] = {}  # 股票代码 -> 持仓均价
        self.trades: List[Dict] = []  # 交易记录
    
    def buy(self, ts_code: str, price: float, quantity: int) -> bool:
        """买入股票"""
        cost = price * quantity
        if self.cash < cost:
            return False
        
        self.cash -= cost
        
        # 更新持仓
        if ts_code in self.positions:
            # 计算新的持仓均价
            total_cost = self.position_prices[ts_code] * self.positions[ts_code] + cost
            total_quantity = self.positions[ts_code] + quantity
            self.position_prices[ts_code] = total_cost / total_quantity
            self.positions[ts_code] += quantity
        else:
            self.positions[ts_code] = quantity
            self.position_prices[ts_code] = price
        
        # 记录交易
        self.trades.append({
            "timestamp": datetime.now(),
            "ts_code": ts_code,
            "side": "buy",
            "price": price,
            "quantity": quantity,
            "value": cost
        })
        
        return True
    
    def sell(self, ts_code: str, price: float, quantity: int) -> bool:
        """卖出股票"""
        if ts_code not in self.positions or self.positions[ts_code] < quantity:
            return False
        
        proceeds = price * quantity
        self.cash += proceeds
        
        # 更新持仓
        self.positions[ts_code] -= quantity
        if self.positions[ts_code] == 0:
            del self.positions[ts_code]
            del self.position_prices[ts_code]
        
        # 记录交易
        self.trades.append({
            "timestamp": datetime.now(),
            "ts_code": ts_code,
            "side": "sell",
            "price": price,
            "quantity": quantity,
            "value": proceeds
        })
        
        return True
    
    def get_total_value(self, market_prices: Dict[str, float]) -> float:
        """计算总资产价值"""
        position_value = sum(
            quantity * market_prices.get(ts_code, 0) 
            for ts_code, quantity in self.positions.items()
        )
        return self.cash + position_value
    
    def get_positions(self) -> Dict[str, Dict]:
        """获取当前持仓信息"""
        return {
            ts_code: {
                "quantity": quantity,
                "avg_price": self.position_prices[ts_code]
            }
            for ts_code, quantity in self.positions.items()
        }


class BacktestEngine:
    """回测引擎类"""
    
    def __init__(self):
        self.matcher = SimpleMatcher()
        self.portfolio = None
        self.price_history = None
        self.daily_values = []
    
    def _generate_dummy_prices(self, stock_pool: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """生成模拟价格数据"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        date_range = pd.date_range(start, end)
        
        prices = {}
        for stock in stock_pool:
            # 为每个股票生成随机价格序列
            base_price = random.uniform(10, 100)
            returns = np.random.normal(0, 0.02, len(date_range))
            close_prices = base_price * np.exp(np.cumsum(returns))
            
            # 生成高低开价格
            open_prices = close_prices * np.random.uniform(0.98, 1.02, len(date_range))
            high_prices = np.maximum(close_prices, open_prices) * np.random.uniform(1.0, 1.03, len(date_range))
            low_prices = np.minimum(close_prices, open_prices) * np.random.uniform(0.97, 1.0, len(date_range))
            
            df = pd.DataFrame({
                'open': open_prices,
                'high': high_prices,
                'low': low_prices,
                'close': close_prices
            }, index=date_range)
            prices[stock] = df
        
        return prices
    
    def _calculate_performance(self) -> Dict[str, float]:
        """计算绩效指标"""
        if not self.daily_values:
            return {}
        
        # 转换为DataFrame便于计算
        df = pd.DataFrame(self.daily_values)
        
        # 计算每日收益率
        df['daily_return'] = df['total_value'].pct_change()
        
        # 计算累计收益率
        total_return = (df['total_value'].iloc[-1] / df['total_value'].iloc[0]) - 1
        
        # 计算年化收益率
        days = (df['date'].iloc[-1] - df['date'].iloc[0]).days
        annual_return = ((1 + total_return) ** (365 / days)) - 1 if days > 0 else 0
        
        # 计算波动率
        volatility = df['daily_return'].std() * np.sqrt(252)  # 年化
        
        # 计算夏普比率（假设无风险利率为0）
        sharpe = annual_return / volatility if volatility > 0 else 0
        
        # 计算最大回撤
        df['cum_max'] = df['total_value'].cummax()
        df['drawdown'] = (df['total_value'] - df['cum_max']) / df['cum_max']
        max_drawdown = df['drawdown'].min()
        
        # 计算胜率
        win_rate = (df['daily_return'] > 0).mean()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': len(self.portfolio.trades) if self.portfolio else 0
        }
    
    def _simple_strategy(self, date: datetime, prices: Dict[str, pd.DataFrame], portfolio: Portfolio) -> None:
        """简单的交易策略示例"""
        # 获取当前价格
        current_prices = {}
        for stock, price_df in prices.items():
            if date in price_df.index:
                current_prices[stock] = price_df.loc[date, 'close']
        
        # 如果持仓为空，随机买入几只股票
        if not portfolio.positions and current_prices:
            stocks_to_buy = random.sample(list(current_prices.keys()), min(3, len(current_prices)))
            for stock in stocks_to_buy:
                price = current_prices[stock]
                # 计算可以买入的数量
                quantity = int(portfolio.cash * 0.2 / price)  # 用20%的现金买入每只股票
                if quantity > 0:
                    portfolio.buy(stock, price, quantity)
        
        # 简单的卖出规则：随机卖出一只持仓股票
        elif portfolio.positions and random.random() < 0.1:  # 10%的概率卖出
            stock_to_sell = random.choice(list(portfolio.positions.keys()))
            if stock_to_sell in current_prices:
                price = current_prices[stock_to_sell]
                quantity = portfolio.positions[stock_to_sell]
                portfolio.sell(stock_to_sell, price, quantity)
    
    def run(self, strategy_id: str, stock_pool: list, start_date: str, end_date: str, init_cash: float, 
            progress_callback=None) -> Dict[str, any]:
        """运行回测"""
        try:
            logger.info(f"Running backtest {strategy_id} on {len(stock_pool)} stocks {start_date}-{end_date}")
            
            # 初始化投资组合
            self.portfolio = Portfolio(init_cash)
            
            # 生成模拟价格数据
            self.price_history = self._generate_dummy_prices(stock_pool, start_date, end_date)
            
            # 解析日期
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            date_range = pd.date_range(start, end)
            
            # 回测主循环
            for i, date in enumerate(date_range):
                # 获取当天的价格
                current_prices = {}
                for stock, price_df in self.price_history.items():
                    if date in price_df.index:
                        row = price_df.loc[date]
                        current_prices[stock] = row['close']
                        
                        # 创建Bar对象用于订单匹配
                        bar = Bar(close=row['close'], low=row['low'], high=row['high'])
                
                # 执行策略
                self._simple_strategy(date, self.price_history, self.portfolio)
                
                # 记录当日资产价值
                total_value = self.portfolio.get_total_value(current_prices)
                self.daily_values.append({
                    'date': date,
                    'total_value': total_value,
                    'cash': self.portfolio.cash,
                    'positions': len(self.portfolio.positions)
                })
                
                # 检查最大回撤
                if len(self.daily_values) > 1:
                    df = pd.DataFrame(self.daily_values)
                    df['cum_max'] = df['total_value'].cummax()
                    df['drawdown'] = (df['total_value'] - df['cum_max']) / df['cum_max']
                    current_dd = df['drawdown'].iloc[-1]
                    
                    if current_dd < -MAX_DD_THRESHOLD:
                        logger.warning(f"Backtest stopped due to maximum drawdown threshold reached: {current_dd:.2%}")
                        break
                
                # 调用进度回调
                if progress_callback:
                    progress = (i + 1) / len(date_range)
                    progress_callback(progress)
            
            # 计算绩效指标
            performance = self._calculate_performance()
            
            # 生成回测结果
            result = {
                'status': 'success',
                'strategy_id': strategy_id,
                'start_date': start_date,
                'end_date': end_date,
                'init_cash': init_cash,
                'final_value': self.portfolio.get_total_value(current_prices),
                'positions': self.portfolio.get_positions(),
                'performance': performance,
                'trade_count': len(self.portfolio.trades)
            }
            
            logger.info(f"Backtest completed: {result['performance']['total_return']:.2%} total return")
            return result
            
        except Exception as e:
            logger.exception("Error running backtest")
            raise BacktestError(
                message=f"Failed to run backtest",
                strategy_id=strategy_id,
                backtest_id=str(time.time())
            ) from e


# 导入numpy供内部使用
import numpy as np
