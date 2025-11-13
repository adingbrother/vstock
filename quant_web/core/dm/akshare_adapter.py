import asyncio
import random
import pandas as pd
import akshare as ak
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta
from loguru import logger

from quant_web.core.const import AK_SLEEP, MAX_RETRY


class AkShareAdapter:
    """
    AkShare数据适配器
    提供与AkShare库的交互接口，用于获取各类股票市场数据
    支持多种数据类型、复权处理和错误重试机制
    """
    
    # 支持的数据类型
    SUPPORTED_DATA_TYPES = {
        'daily': '日线数据',
        'minute': '分钟线数据',
        'weekly': '周线数据',
        'monthly': '月线数据',
        'finance': '财务数据',
        'indicator': '技术指标'
    }
    
    # 支持的复权类型
    ADJUST_TYPES = {
        'None': None,  # 不复权
        'Forward': 'qfq',  # 前复权
        'Backward': 'hfq'  # 后复权
    }
    
    def __init__(self):
        """初始化AkShare适配器"""
        self.logger = logger.bind(component="AkShareAdapter")
        # 数据源信息
        self.source_info = {
            'source_id': 'akshare',
            'name': 'AkShare金融数据接口',
            'description': '提供A股、港股、美股等全球金融数据',
            'supported_data_types': list(self.SUPPORTED_DATA_TYPES.keys()),
            'is_active': True
        }
    
    async def download_daily(self, ts_code: str, start: str, end: str, adjust_type: str = 'None') -> pd.DataFrame:
        """
        下载股票日线数据
        
        Args:
            ts_code: 股票代码，格式如 '000001.SZ'
            start: 开始日期，格式如 '20230101'
            end: 结束日期，格式如 '20231231'
            adjust_type: 复权类型，可选 'None'、'Forward'、'Backward'
            
        Returns:
            标准化的日线数据DataFrame，包含列：[trade_date, open, high, low, close, vol, amount, adjust_flag]
        """
        for attempt in range(1, MAX_RETRY + 1):
            try:
                code = self._to_ak_code(ts_code)
                adjust = self.ADJUST_TYPES.get(adjust_type, None)
                
                # 调用AkShare获取数据
                df = await asyncio.to_thread(
                    ak.stock_zh_a_hist,
                    symbol=code,
                    period="daily",
                    start_date=start,
                    end_date=end,
                    adjust=adjust
                )
                
                # 数据质量检查
                if df is None or df.empty:
                    raise ValueError(f"AkShare 返回空数据 {ts_code} 尝试={attempt}")
                
                # 标准化列名和格式
                df = self._normalize_daily_data(df, ts_code, adjust_type)
                
                # 数据验证和清洗
                df = self._validate_and_clean_data(df)
                
                # 遵守API调用频率限制
                await asyncio.sleep(AK_SLEEP)
                self.logger.info(f"AkShare 下载完成 {ts_code} {len(df)} 条数据，复权类型: {adjust_type}")
                return df
            except Exception as e:
                self.logger.warning(f"AkShare 下载失败 {ts_code} 尝试={attempt} {e}")
                if attempt == MAX_RETRY:
                    # 最后一次尝试失败，记录详细错误
                    self.logger.error(f"AkShare 下载失败（已达最大重试次数） {ts_code}: {str(e)}")
                    raise
                # 指数退避 + 随机抖动
                backoff_time = (2 ** (attempt - 1)) + random.uniform(0, 1)
                self.logger.debug(f"将在 {backoff_time:.2f} 秒后重试")
                await asyncio.sleep(backoff_time)
    
    async def download_minute(self, ts_code: str, period: str = '1', adjust_type: str = 'None') -> pd.DataFrame:
        """
        下载股票分钟线数据
        
        Args:
            ts_code: 股票代码，格式如 '000001.SZ'
            period: K线周期，可选 '1'、'5'、'15'、'30'、'60'分钟
            adjust_type: 复权类型，可选 'None'、'Forward'、'Backward'
            
        Returns:
            标准化的分钟线数据DataFrame
        """
        valid_periods = ['1', '5', '15', '30', '60']
        if period not in valid_periods:
            raise ValueError(f"无效的分钟线周期: {period}，有效值: {', '.join(valid_periods)}")
        
        for attempt in range(1, MAX_RETRY + 1):
            try:
                code = self._to_ak_code(ts_code)
                adjust = self.ADJUST_TYPES.get(adjust_type, None)
                
                # 调用AkShare获取分钟线数据
                df = await asyncio.to_thread(
                    ak.stock_zh_a_minute,
                    symbol=code,
                    period=period,
                    adjust=adjust
                )
                
                if df is None or df.empty:
                    raise ValueError(f"AkShare 返回空分钟线数据 {ts_code} 周期={period}")
                
                # 标准化列名和格式
                df = df.rename(columns={
                    "时间": "trade_time", "开盘": "open", "收盘": "close", 
                    "最高": "high", "最低": "low", "成交量": "vol"
                })
                
                # 添加股票代码和来源信息
                df["ts_code"] = ts_code
                df["source"] = "akshare"
                df["adjust_flag"] = adjust_type
                df["period"] = period
                
                await asyncio.sleep(AK_SLEEP)
                self.logger.info(f"AkShare 下载完成 {ts_code} 分钟线数据 {len(df)} 条，周期: {period}分钟")
                return df
            except Exception as e:
                self.logger.warning(f"AkShare 分钟线下载失败 {ts_code} 尝试={attempt} {e}")
                if attempt == MAX_RETRY:
                    raise
                await asyncio.sleep((2 ** (attempt - 1)) + random.uniform(0, 1))
    
    async def download_batch(self, stock_pool: List[str], start: str, end: str, 
                           adjust_type: str = 'None', max_concurrency: int = 3) -> Dict[str, pd.DataFrame]:
        """
        批量下载股票数据
        
        Args:
            stock_pool: 股票代码列表
            start: 开始日期
            end: 结束日期
            adjust_type: 复权类型
            max_concurrency: 最大并发数
            
        Returns:
            股票代码到数据的映射字典
        """
        results = {}
        errors = {}
        
        # 创建并发任务，但限制最大并发数
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def download_one(code):
            async with semaphore:
                try:
                    data = await self.download_daily(code, start, end, adjust_type)
                    results[code] = data
                    return (code, True)
                except Exception as e:
                    errors[code] = str(e)
                    return (code, False)
        
        # 并发执行下载任务
        tasks = [download_one(code) for code in stock_pool]
        self.logger.info(f"开始批量下载 {len(stock_pool)} 只股票数据")
        
        # 使用 gather 收集所有任务结果
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 统计下载结果
        success_count = sum(1 for _, success in completed_tasks if success)
        self.logger.info(f"批量下载完成：成功 {success_count}/{len(stock_pool)} 只股票")
        
        if errors:
            self.logger.warning(f"以下股票下载失败：{list(errors.keys())}")
            for code, error in errors.items():
                self.logger.debug(f"{code} 失败原因: {error}")
        
        return results
    
    async def get_stock_basic(self) -> pd.DataFrame:
        """
        获取A股股票基础信息
        
        Returns:
            包含股票代码、名称、行业等信息的DataFrame
        """
        for attempt in range(1, MAX_RETRY + 1):
            try:
                df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
                
                if df is None or df.empty:
                    raise ValueError("获取股票基础信息失败：返回空数据")
                
                # 标准化列名和格式
                df = df.rename(columns={
                    "代码": "ts_code", "名称": "name", "所属行业": "industry",
                    "最新价": "price", "涨跌幅": "pct_change"
                })
                
                # 处理股票代码格式，确保包含交易所标识
                df['ts_code'] = df['ts_code'].apply(self._format_stock_code)
                
                await asyncio.sleep(AK_SLEEP)
                self.logger.info(f"获取股票基础信息成功，共 {len(df)} 条")
                return df
            except Exception as e:
                self.logger.warning(f"获取股票基础信息失败 尝试={attempt} {e}")
                if attempt == MAX_RETRY:
                    raise
                await asyncio.sleep((2 ** (attempt - 1)) + random.uniform(0, 1))
    
    async def get_index_constituents(self, index_code: str) -> List[str]:
        """
        获取指数成分股
        
        Args:
            index_code: 指数代码，如 '000001' 表示上证指数
            
        Returns:
            成分股代码列表
        """
        for attempt in range(1, MAX_RETRY + 1):
            try:
                # 获取指数成分股
                df = await asyncio.to_thread(
                    ak.index_stock_cons,
                    symbol=index_code
                )
                
                if df is None or df.empty:
                    raise ValueError(f"获取指数 {index_code} 成分股失败：返回空数据")
                
                # 提取股票代码并格式化
                stock_codes = []
                for _, row in df.iterrows():
                    # 根据不同指数，列名可能不同
                    if '成分券代码' in row:
                        code = str(row['成分券代码']).zfill(6)
                        stock_codes.append(self._format_stock_code(code))
                    elif '品种代码' in row:
                        code = str(row['品种代码']).zfill(6)
                        stock_codes.append(self._format_stock_code(code))
                    elif '代码' in row:
                        code = str(row['代码']).zfill(6)
                        stock_codes.append(self._format_stock_code(code))
                
                await asyncio.sleep(AK_SLEEP)
                self.logger.info(f"获取指数 {index_code} 成分股成功，共 {len(stock_codes)} 只")
                return stock_codes
            except Exception as e:
                self.logger.warning(f"获取指数成分股失败 尝试={attempt} {e}")
                if attempt == MAX_RETRY:
                    raise
                await asyncio.sleep((2 ** (attempt - 1)) + random.uniform(0, 1))
    
    def _normalize_daily_data(self, df: pd.DataFrame, ts_code: str, adjust_type: str) -> pd.DataFrame:
        """标准化日线数据格式"""
        # 标准化列名
        df = df.rename(columns={
            "日期": "trade_date", "开盘": "open", "收盘": "close", 
            "最高": "high", "最低": "low", "成交量": "vol", "成交额": "amount"
        })
        
        # 确保日期格式一致
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y%m%d")
        
        # 添加额外信息
        df["ts_code"] = ts_code
        df["source"] = "akshare"
        df["adjust_flag"] = adjust_type
        
        # 确保数值列格式正确
        numeric_cols = ["open", "high", "low", "close", "vol", "amount"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def _validate_and_clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """验证并清洗数据"""
        # 删除重复行
        df = df.drop_duplicates(subset=['trade_date'], keep='first')
        
        # 删除NaN值
        df = df.dropna(subset=['open', 'high', 'low', 'close'])
        
        # 检查异常值（价格不能为负）
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            if col in df.columns:
                df = df[df[col] > 0]
        
        # 确保数据按日期排序
        if 'trade_date' in df.columns:
            df = df.sort_values('trade_date')
        
        return df
    
    def _to_ak_code(self, ts_code: str) -> str:
        """将标准股票代码转换为AkShare使用的代码格式"""
        # 从 000001.SZ 转换为 000001
        return ts_code.split('.')[0]
    
    def _format_stock_code(self, code: str) -> str:
        """将6位数字代码格式化为标准格式（添加交易所后缀）"""
        # 确保代码是6位
        code = str(code).zfill(6)
        
        # 根据代码前缀判断交易所
        if code.startswith(('000', '001', '002', '003', '004', '005', '006', '007', '008', '009', '300', '301')):
            return f"{code}.SZ"  # 深圳
        elif code.startswith(('600', '601', '603', '605', '688', '689')):
            return f"{code}.SH"  # 上海
        else:
            return code  # 无法判断的代码保持原样
    
    async def get_data_statistics(self) -> Dict[str, any]:
        """
        获取数据源统计信息
        
        Returns:
            包含数据源统计信息的字典
        """
        try:
            # 获取股票数量
            basic_df = await self.get_stock_basic()
            
            # 获取上证指数成分股数量
            try:
                sz50_stocks = await self.get_index_constituents('000016')  # 上证50
                sz50_count = len(sz50_stocks)
            except:
                sz50_count = 0
            
            return {
                'total_stocks': len(basic_df),
                'sz50_count': sz50_count,
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'source': 'akshare',
                'supported_data_types': list(self.SUPPORTED_DATA_TYPES.keys())
            }
        except Exception as e:
            self.logger.error(f"获取数据统计信息失败: {e}")
            return {
                'error': str(e),
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    async def verify_data_availability(self, stock_codes: List[str], start_date: str, end_date: str) -> Dict[str, bool]:
        """
        验证多只股票的数据可用性
        
        Args:
            stock_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            股票代码到可用性的映射字典
        """
        availability = {}
        
        # 对于批量验证，降低重试次数以提高效率
        # 先声明全局变量
        global MAX_RETRY
        original_max_retry = MAX_RETRY
        try:
            # 临时修改最大重试次数
            MAX_RETRY = 1
            
            for code in stock_codes:
                try:
                    # 只获取少量数据进行验证
                    df = await self.download_daily(code, start_date, end_date, 'None')
                    availability[code] = len(df) > 0
                except:
                    availability[code] = False
        finally:
            # 恢复原始重试次数
            MAX_RETRY = original_max_retry
        
        return availability
    
    def get_source_info(self) -> Dict[str, any]:
        """
        获取数据源信息
        
        Returns:
            数据源信息字典
        """
        return self.source_info
