from enum import Enum
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict


class OrderSide(Enum):
    """订单方向枚举"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """订单状态枚举"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """订单类，用于表示交易订单"""
    order_id: str  # 订单ID
    strategy_id: str  # 策略ID
    ts_code: str  # 股票代码
    side: str  # 交易方向（buy/sell）
    quantity: int  # 数量
    price: Optional[float] = None  # 价格
    signal_type: str = "unknown"  # 信号类型
    status: OrderStatus = OrderStatus.PENDING  # 订单状态
    created_at: Optional[datetime] = None  # 创建时间
    filled_at: Optional[datetime] = None  # 成交时间
    filled_price: Optional[float] = None  # 成交价格
    filled_quantity: int = 0  # 成交数量
    commission: float = 0.0  # 佣金
    message: str = ""  # 状态消息
    
    def __post_init__(self):
        # 初始化创建时间
        if self.created_at is None:
            self.created_at = datetime.now()
        
        # 验证交易方向
        if self.side not in [OrderSide.BUY.value, OrderSide.SELL.value]:
            raise ValueError(f"Invalid order side: {self.side}")
        
        # 验证数量
        if self.quantity <= 0:
            raise ValueError(f"Order quantity must be positive: {self.quantity}")
    
    def fill(self, fill_date: datetime, fill_price: Optional[float] = None) -> bool:
        """成交订单
        
        Args:
            fill_date: 成交日期
            fill_price: 成交价格，如果为None则使用订单价格
            
        Returns:
            是否成功成交
        """
        if self.status != OrderStatus.PENDING:
            self.message = f"Cannot fill order in status: {self.status.value}"
            return False
        
        # 设置成交价格
        if fill_price is not None:
            self.filled_price = fill_price
        elif self.price is not None:
            self.filled_price = self.price
        else:
            self.message = "No price specified for order"
            return False
        
        # 更新订单状态
        self.status = OrderStatus.FILLED
        self.filled_at = fill_date
        self.filled_quantity = self.quantity
        self.message = "Order filled completely"
        
        return True
    
    def cancel(self, cancel_date: datetime, reason: str = "") -> bool:
        """取消订单
        
        Args:
            cancel_date: 取消日期
            reason: 取消原因
            
        Returns:
            是否成功取消
        """
        if self.status != OrderStatus.PENDING:
            self.message = f"Cannot cancel order in status: {self.status.value}"
            return False
        
        # 更新订单状态
        self.status = OrderStatus.CANCELLED
        self.message = reason or "Order cancelled"
        
        return True
    
    def reject(self, reason: str = "") -> bool:
        """拒绝订单
        
        Args:
            reason: 拒绝原因
            
        Returns:
            是否成功拒绝
        """
        if self.status != OrderStatus.PENDING:
            self.message = f"Cannot reject order in status: {self.status.value}"
            return False
        
        # 更新订单状态
        self.status = OrderStatus.REJECTED
        self.message = reason or "Order rejected"
        
        return True
    
    def is_filled(self) -> bool:
        """检查订单是否已成交"""
        return self.status == OrderStatus.FILLED
    
    def is_cancelled(self) -> bool:
        """检查订单是否已取消"""
        return self.status == OrderStatus.CANCELLED
    
    def is_rejected(self) -> bool:
        """检查订单是否已拒绝"""
        return self.status == OrderStatus.REJECTED
    
    def is_pending(self) -> bool:
        """检查订单是否处于待处理状态"""
        return self.status == OrderStatus.PENDING
    
    def get_value(self) -> float:
        """获取订单价值"""
        price = self.filled_price if self.filled_price is not None else self.price
        if price is None:
            return 0.0
        return price * self.quantity
    
    def to_dict(self) -> dict:
        """将订单转换为字典格式"""
        order_dict = asdict(self)
        # 转换枚举类型为字符串
        order_dict['status'] = self.status.value
        # 转换日期为字符串
        if self.created_at:
            order_dict['created_at'] = self.created_at.isoformat()
        if self.filled_at:
            order_dict['filled_at'] = self.filled_at.isoformat()
        return order_dict
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Order':
        """从字典创建订单实例"""
        # 处理状态枚举
        if 'status' in data:
            data['status'] = OrderStatus(data['status'])
        # 处理日期
        for date_field in ['created_at', 'filled_at']:
            if date_field in data and data[date_field]:
                data[date_field] = datetime.fromisoformat(data[date_field])
        return cls(**data)
    
    def __str__(self) -> str:
        """字符串表示"""
        return (f"Order(id={self.order_id}, {self.side} {self.quantity} shares of {self.ts_code} "
                f"@{self.price}, status={self.status.value})")
