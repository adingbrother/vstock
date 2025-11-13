from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger


class DataFeed:
    """数据馈送类，负责提供历史和实时市场数据"""
    
    def __init__(self):
        self.stock_data: Dict[str, pd.DataFrame] = {}
        self.stock_codes: List[str] = []
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
    
    def load_historical_data(self, ts_codes: List[str], start_date: datetime, end_date: datetime) -> bool:
        """加载历史数据
        
        Args:
            ts_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            是否加载成功
        """
        try:
            self.start_date = start_date
            self.end_date = end_date
            self.stock_codes = ts_codes
            
            # 模拟生成历史数据
            for ts_code in ts_codes:
                self.stock_data[ts_code] = self._generate_sample_data(ts_code, start_date, end_date)
            
            logger.info(f"Loaded historical data for {len(ts_codes)} stocks from {start_date} to {end_date}")
            return True
        except Exception as e:
            logger.error(f"Failed to load historical data: {str(e)}")
            return False
    
    def _generate_sample_data(self, ts_code: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """生成模拟的股票历史数据"""
        # 生成日期序列
        date_range = pd.date_range(start=start_date, end=end_date)
        
        # 过滤非交易日（简单模拟，假设只有周一到周五是交易日）
        trading_days = [date for date in date_range if date.weekday() < 5]
        
        # 随机种子，保证同一只股票生成相同的数据
        np.random.seed(hash(ts_code) % 1000)
        
        # 生成价格数据
        n_days = len(trading_days)
        
        # 初始价格
        initial_price = 10 + np.random.rand() * 90  # 10-100之间的随机初始价格
        
        # 生成随机收益
        daily_returns = np.random.normal(0.0002, 0.01, n_days)  # 平均每天0.02%的收益，波动率1%
        
        # 计算价格序列
        prices = initial_price * (1 + daily_returns).cumprod()
        
        # 生成OHLC数据（开盘价、最高价、最低价、收盘价）
        open_prices = prices * (1 + np.random.normal(0, 0.001, n_days))
        high_prices = np.maximum(prices * (1 + np.random.uniform(0.001, 0.03, n_days)), np.maximum(open_prices, prices))
        low_prices = np.minimum(prices * (1 - np.random.uniform(0.001, 0.03, n_days)), np.minimum(open_prices, prices))
        close_prices = prices
        
        # 生成成交量
        volumes = np.random.randint(1000000, 100000000, n_days)  # 100万到1亿股之间
        
        # 创建DataFrame
        df = pd.DataFrame({
            'date': trading_days,
            'ts_code': ts_code,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes,
            'amount': volumes * close_prices  # 成交额
        })
        
        # 设置日期索引
        df.set_index('date', inplace=True)
        
        # 格式化价格为两位小数
        price_columns = ['open', 'high', 'low', 'close']
        df[price_columns] = df[price_columns].round(2)
        
        return df
    
    def get_data_for_date(self, date: datetime) -> Dict[str, pd.DataFrame]:
        """获取指定日期的数据
        
        Args:
            date: 日期
            
        Returns:
            股票数据字典，格式为 {ts_code: dataframe}
        """
        data = {}
        
        for ts_code, df in self.stock_data.items():
            # 检查是否有该日期的数据
            if date in df.index:
                # 返回包含该日期的数据窗口（需要足够的历史数据来计算技术指标）
                # 这里返回过去60天的数据，确保有足够的历史数据
                start_idx = max(0, df.index.get_loc(date) - 60)
                data_window = df.iloc[start_idx:df.index.get_loc(date) + 1]
                data[ts_code] = data_window
        
        return data
    
    def get_trading_dates(self, start_date: datetime, end_date: datetime) -> List[datetime]:
        """获取交易日期列表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易日期列表
        """
        if not self.stock_data:
            # 如果没有数据，生成模拟的交易日历
            date_range = pd.date_range(start=start_date, end=end_date)
            trading_days = [date for date in date_range if date.weekday() < 5]
            return trading_days
        
        # 从第一只股票的数据中获取交易日历
        first_stock = next(iter(self.stock_data.values()), None)
        if first_stock is not None:
            # 过滤日期范围内的交易日
            mask = (first_stock.index >= start_date) & (first_stock.index <= end_date)
            return list(first_stock.index[mask])
        
        return []
    
    def get_available_stocks(self) -> List[str]:
        """获取可用的股票代码列表"""
        return self.stock_codes
    
    def get_stock_data(self, ts_code: str) -> Optional[pd.DataFrame]:
        """获取指定股票的完整历史数据"""
        return self.stock_data.get(ts_code)
    
    def get_latest_price(self, ts_code: str) -> Optional[float]:
        """获取指定股票的最新价格"""
        if ts_code in self.stock_data and not self.stock_data[ts_code].empty:
            return self.stock_data[ts_code]['close'].iloc[-1]
        return None
    
    def get_price_range(self, ts_code: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """获取指定日期范围内的价格数据"""
        if ts_code in self.stock_data:
            mask = (self.stock_data[ts_code].index >= start_date) & (self.stock_data[ts_code].index <= end_date)
            return self.stock_data[ts_code][mask]
        return None
    
    def update_with_realtime(self, date: datetime, prices: Dict[str, float]) -> None:
        """更新实时价格数据（用于模拟实时交易）
        
        Args:
            date: 当前日期
            prices: 股票价格字典，格式为 {ts_code: price}
        """
        for ts_code, price in prices.items():
            if ts_code in self.stock_data:
                # 创建新的行数据
                last_row = self.stock_data[ts_code].iloc[-1]
                new_row = pd.DataFrame({
                    'ts_code': [ts_code],
                    'open': [last_row['close']],  # 以昨天的收盘价作为今天的开盘价
                    'high': [max(last_row['close'], price)],
                    'low': [min(last_row['close'], price)],
                    'close': [price],
                    'volume': [np.random.randint(1000000, 100000000)],
                    'amount': [price * np.random.randint(1000000, 100000000)]
                }, index=[date])
                
                # 添加到现有数据中
                self.stock_data[ts_code] = pd.concat([self.stock_data[ts_code], new_row])
    
    def save_data(self, file_path: str) -> bool:
        """保存数据到文件（可选功能）"""
        try:
            # 将所有股票数据保存到单个HDF5文件
            with pd.HDFStore(file_path) as store:
                for ts_code, df in self.stock_data.items():
                    store.put(ts_code, df)
            logger.info(f"Data saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save data: {str(e)}")
            return False
    
    def load_data(self, file_path: str) -> bool:
        """从文件加载数据（可选功能）"""
        try:
            with pd.HDFStore(file_path) as store:
                self.stock_data = {}
                self.stock_codes = []
                for key in store.keys():
                    # 移除开头的'/'
                    ts_code = key[1:]
                    self.stock_data[ts_code] = store.get(key)
                    self.stock_codes.append(ts_code)
                    
                # 更新日期范围
                if self.stock_data:
                    first_stock = next(iter(self.stock_data.values()))
                    self.start_date = first_stock.index.min()
                    self.end_date = first_stock.index.max()
            
            logger.info(f"Data loaded from {file_path}, {len(self.stock_codes)} stocks available")
            return True
        except Exception as e:
            logger.error(f"Failed to load data: {str(e)}")
            return False
