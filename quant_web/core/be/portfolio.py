from typing import Dict, Optional
import pandas as pd
from loguru import logger


class Portfolio:
    """投资组合管理类，负责管理现金、持仓和交易执行"""
    
    def __init__(self, initial_cash: float = 1000000.0):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, int] = {}  # 持仓 {ts_code: quantity}
        self.position_costs: Dict[str, float] = {}  # 持仓成本 {ts_code: avg_cost}
        self.total_commission = 0.0  # 总佣金
        logger.info(f"Portfolio initialized with cash: {initial_cash}")
    
    def reset(self) -> None:
        """重置投资组合"""
        self.cash = self.initial_cash
        self.positions = {}
        self.position_costs = {}
        self.total_commission = 0.0
        logger.info("Portfolio reset")
    
    def buy(self, ts_code: str, quantity: int, price: float, commission_rate: float = 0.0003) -> bool:
        """买入股票
        
        Args:
            ts_code: 股票代码
            quantity: 买入数量
            price: 买入价格
            commission_rate: 佣金率
            
        Returns:
            是否成功买入
        """
        # 计算交易成本
        cost = price * quantity
        commission = max(cost * commission_rate, 5.0)  # 最低佣金5元
        total_cost = cost + commission
        
        # 检查资金是否足够
        if self.cash < total_cost:
            logger.warning(f"Insufficient cash for buy order: {ts_code} - Need {total_cost}, Available {self.cash}")
            return False
        
        # 更新现金
        self.cash -= total_cost
        
        # 更新持仓
        if ts_code in self.positions:
            # 已持有该股票，计算平均成本
            total_shares = self.positions[ts_code] + quantity
            total_cost_basis = (self.position_costs[ts_code] * self.positions[ts_code]) + cost
            self.position_costs[ts_code] = total_cost_basis / total_shares
            self.positions[ts_code] = total_shares
        else:
            # 首次买入
            self.positions[ts_code] = quantity
            self.position_costs[ts_code] = price
        
        self.total_commission += commission
        logger.info(f"Bought {quantity} shares of {ts_code} at {price}, Cash remaining: {self.cash}")
        return True
    
    def sell(self, ts_code: str, quantity: int, price: float, commission_rate: float = 0.0003) -> bool:
        """卖出股票
        
        Args:
            ts_code: 股票代码
            quantity: 卖出数量
            price: 卖出价格
            commission_rate: 佣金率
            
        Returns:
            是否成功卖出
        """
        # 检查持仓是否足够
        if ts_code not in self.positions or self.positions[ts_code] < quantity:
            logger.warning(f"Insufficient shares for sell order: {ts_code} - Requested {quantity}, Available {self.positions.get(ts_code, 0)}")
            return False
        
        # 计算交易收入和成本
        revenue = price * quantity
        commission = max(revenue * commission_rate, 5.0)  # 最低佣金5元
        tax = revenue * 0.001  # 印花税
        net_revenue = revenue - commission - tax
        
        # 更新现金
        self.cash += net_revenue
        
        # 更新持仓
        self.positions[ts_code] -= quantity
        
        # 如果持仓为0，移除该股票
        if self.positions[ts_code] == 0:
            del self.positions[ts_code]
            del self.position_costs[ts_code]
        
        self.total_commission += commission
        logger.info(f"Sold {quantity} shares of {ts_code} at {price}, Cash remaining: {self.cash}")
        return True
    
    def can_buy(self, ts_code: str, quantity: int, price: float, commission_rate: float = 0.0003) -> bool:
        """检查是否可以买入指定数量的股票"""
        cost = price * quantity
        commission = max(cost * commission_rate, 5.0)
        total_cost = cost + commission
        return self.cash >= total_cost
    
    def can_sell(self, ts_code: str, quantity: int) -> bool:
        """检查是否可以卖出指定数量的股票"""
        return ts_code in self.positions and self.positions[ts_code] >= quantity
    
    def get_position_value(self, ts_code: str, current_price: float) -> float:
        """获取单个持仓的当前市值"""
        if ts_code not in self.positions:
            return 0.0
        return self.positions[ts_code] * current_price
    
    def get_total_value(self, market_data: Dict[str, pd.DataFrame]) -> float:
        """计算投资组合总价值
        
        Args:
            market_data: 市场数据，格式为 {ts_code: dataframe}
            
        Returns:
            投资组合总价值（现金 + 持仓市值）
        """
        # 计算持仓市值
        positions_value = 0.0
        
        for ts_code, quantity in self.positions.items():
            if ts_code in market_data and not market_data[ts_code].empty:
                current_price = market_data[ts_code]['close'].iloc[-1]
                positions_value += quantity * current_price
        
        # 总价值 = 现金 + 持仓市值
        total_value = self.cash + positions_value
        return total_value
    
    def get_holdings(self) -> Dict[str, Dict]:
        """获取当前持仓详情"""
        holdings = {}
        
        for ts_code, quantity in self.positions.items():
            holdings[ts_code] = {
                'quantity': quantity,
                'avg_cost': self.position_costs.get(ts_code, 0.0)
            }
        
        return holdings
    
    def get_pnl(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """计算盈亏情况
        
        Args:
            market_data: 市场数据，格式为 {ts_code: dataframe}
            
        Returns:
            盈亏信息，包括总体盈亏和各股票盈亏
        """
        total_pnl = 0.0
        stock_pnl = {}
        
        for ts_code, quantity in self.positions.items():
            if ts_code in market_data and not market_data[ts_code].empty:
                current_price = market_data[ts_code]['close'].iloc[-1]
                avg_cost = self.position_costs.get(ts_code, 0.0)
                pnl = (current_price - avg_cost) * quantity
                stock_pnl[ts_code] = pnl
                total_pnl += pnl
        
        return {
            'total_pnl': total_pnl,
            'stock_pnl': stock_pnl
        }
    
    def to_dict(self) -> Dict:
        """将投资组合转换为字典格式"""
        return {
            'initial_cash': self.initial_cash,
            'current_cash': self.cash,
            'positions': self.positions,
            'position_costs': self.position_costs,
            'total_commission': self.total_commission,
            'positions_count': len(self.positions)
        }
    
    def summary(self) -> str:
        """获取投资组合摘要"""
        summary = f"Portfolio Summary:\n"
        summary += f"Initial Cash: {self.initial_cash}\n"
        summary += f"Current Cash: {self.cash}\n"
        summary += f"Total Commission: {self.total_commission}\n"
        summary += f"Holdings: {len(self.positions)}\n"
        
        if self.positions:
            summary += "Positions:\n"
            for ts_code, quantity in sorted(self.positions.items()):
                avg_cost = self.position_costs.get(ts_code, 0.0)
                summary += f"  {ts_code}: {quantity} shares @ avg cost {avg_cost}\n"
        
        return summary
