from typing import Dict, List, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class Bar:
    """K线数据类"""
    close: float
    high: float
    low: float
    open: Optional[float] = None
    volume: Optional[float] = None
    amount: Optional[float] = None


@dataclass
class Order:
    """订单类"""
    order_id: str
    ts_code: str
    side: str  # 'buy' 或 'sell'
    quantity: int
    price: Optional[float] = None  # None 表示市价单
    order_type: str = 'market'  # 'market' 或 'limit'
    status: str = 'pending'  # 'pending', 'filled', 'partially_filled', 'cancelled'
    filled_quantity: int = 0
    filled_price: Optional[float] = None
    timestamp: Optional[float] = None


@dataclass
class Trade:
    """成交记录类"""
    order_id: str
    ts_code: str
    side: str
    price: float
    quantity: int
    timestamp: float


class SimpleMatcher:
    """简单的订单匹配器"""
    
    def __init__(self):
        self.orders: List[Order] = []
        self.trades: List[Trade] = []
    
    def add_order(self, order: Order) -> Order:
        """添加订单"""
        self.orders.append(order)
        logger.debug(f"Added order: {order}")
        return order
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        for order in self.orders:
            if order.order_id == order_id and order.status != 'filled':
                order.status = 'cancelled'
                logger.debug(f"Cancelled order: {order_id}")
                return True
        return False
    
    def match_orders(self, bar: Bar, ts_code: str) -> List[Trade]:
        """匹配订单（基于当前K线）"""
        # 过滤出当前股票的未完成订单
        pending_orders = [
            order for order in self.orders 
            if order.ts_code == ts_code and order.status in ['pending', 'partially_filled']
        ]
        
        new_trades = []
        
        for order in pending_orders:
            # 使用收盘价作为成交价格（简化处理）
            exec_price = bar.close
            
            # 计算可成交数量
            remaining_quantity = order.quantity - order.filled_quantity
            
            # 执行成交
            order.filled_quantity += remaining_quantity
            order.filled_price = exec_price
            order.status = 'filled'
            
            # 创建成交记录
            trade = Trade(
                order_id=order.order_id,
                ts_code=order.ts_code,
                side=order.side,
                price=exec_price,
                quantity=remaining_quantity,
                timestamp=bar.timestamp if hasattr(bar, 'timestamp') else 0.0
            )
            
            self.trades.append(trade)
            new_trades.append(trade)
            
            logger.debug(f"Order filled: {order.order_id}, price: {exec_price}, quantity: {remaining_quantity}")
        
        return new_trades
    
    def get_order_status(self, order_id: str) -> Optional[Order]:
        """获取订单状态"""
        for order in self.orders:
            if order.order_id == order_id:
                return order
        return None
    
    def clear_orders(self) -> None:
        """清除所有订单"""
        self.orders.clear()
        logger.debug("Cleared all orders")
    
    def get_active_orders(self, ts_code: Optional[str] = None) -> List[Order]:
        """获取活跃订单"""
        active_orders = [
            order for order in self.orders 
            if order.status in ['pending', 'partially_filled']
        ]
        
        if ts_code:
            active_orders = [o for o in active_orders if o.ts_code == ts_code]
        
        return active_orders
