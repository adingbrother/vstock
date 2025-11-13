import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class DataLoader:
    """数据加载器基类"""
    
    def __init__(self):
        self.cache = {}
    
    def load_price_data(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """加载价格数据"""
        raise NotImplementedError
    
    def load_batch(self, stock_pool: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """批量加载数据"""
        result = {}
        for ts_code in stock_pool:
            data = self.load_price_data(ts_code, start_date, end_date)
            if data is not None:
                result[ts_code] = data
        return result
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self.cache.clear()


class CSVDataLoader(DataLoader):
    """CSV文件数据加载器"""
    
    def __init__(self, data_dir: str):
        super().__init__()
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            logger.warning(f"Data directory does not exist: {data_dir}")
    
    def load_price_data(self, ts_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """从CSV文件加载价格数据"""
        cache_key = f"{ts_code}_{start_date}_{end_date}"
        
        # 检查缓存
        if cache_key in self.cache:
            logger.debug(f"Returning cached data for {ts_code}")
            return self.cache[cache_key]
        
        # 构建文件路径
        file_path = os.path.join(self.data_dir, f"{ts_code}.csv")
        if not os.path.exists(file_path):
            logger.warning(f"Data file not found: {file_path}")
            return None
        
        try:
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 处理日期列
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
            elif 'trade_date' in df.columns:
                df['trade_date'] = pd.to_datetime(df['trade_date'])
                df.set_index('trade_date', inplace=True)
            
            # 过滤日期范围
            df = df.loc[start_date:end_date]
            
            # 缓存数据
            self.cache[cache_key] = df
            logger.debug(f"Loaded data for {ts_code}, shape: {df.shape}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading data for {ts_code}: {e}")
            return None


class MockDataLoader(DataLoader):
    """模拟数据加载器，用于测试"""
    
    def __init__(self):
        super().__init__()
        self.seed = 42
        np.random.seed(self.seed)
    
    def load_price_data(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """生成模拟价格数据"""
        cache_key = f"{ts_code}_{start_date}_{end_date}"
        
        # 检查缓存
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 生成日期范围
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        date_range = pd.date_range(start, end)
        
        # 为每个股票生成随机价格序列（基于股票代码生成不同的随机序列）
        stock_seed = hash(ts_code) % 10000
        np.random.seed(stock_seed)
        
        # 生成基础价格
        base_price = np.random.uniform(10, 100)
        
        # 生成随机收益率序列
        daily_returns = np.random.normal(0, 0.02, len(date_range))
        
        # 计算价格序列
        close_prices = base_price * np.exp(np.cumsum(daily_returns))
        
        # 生成开盘价、最高价、最低价
        open_prices = close_prices * np.random.uniform(0.98, 1.02, len(date_range))
        high_prices = np.maximum(close_prices, open_prices) * np.random.uniform(1.0, 1.03, len(date_range))
        low_prices = np.minimum(close_prices, open_prices) * np.random.uniform(0.97, 1.0, len(date_range))
        
        # 生成成交量
        volumes = np.random.randint(1000000, 100000000, len(date_range))
        
        # 创建DataFrame
        df = pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes,
            'amount': close_prices * volumes,
            'ts_code': ts_code
        }, index=date_range)
        
        # 缓存数据
        self.cache[cache_key] = df
        
        return df


class DataLoaderFactory:
    """数据加载器工厂类"""
    
    @classmethod
    def create(cls, loader_type: str, **kwargs) -> DataLoader:
        """创建数据加载器实例"""
        if loader_type == 'csv':
            return CSVDataLoader(**kwargs)
        elif loader_type == 'mock':
            return MockDataLoader(**kwargs)
        else:
            raise ValueError(f"Unknown data loader type: {loader_type}")
