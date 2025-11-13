import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from quant_web.core.dm.akshare_adapter import AkShareAdapter
from quant_web.core.const import AK_SLEEP, MAX_RETRY
import pandas as pd
import numpy as np


@pytest.fixture
def ak_adapter():
    """创建AkShareAdapter实例作为测试夹具"""
    return AkShareAdapter()


@pytest.fixture
def sample_akshare_daily_data():
    """提供模拟的AkShare日线数据"""
    return pd.DataFrame({
        '日期': ['2023-01-03', '2023-01-04', '2023-01-05'],
        '开盘': [10.0, 10.5, 11.0],
        '最高': [10.5, 11.0, 11.5],
        '最低': [9.9, 10.4, 10.9],
        '收盘': [10.3, 10.8, 11.2],
        '成交量': [1000000, 1200000, 1500000],
        '成交额': [10300000, 12960000, 16800000]
    })


# 同步版本的夹具，用于测试非异步方法
@pytest.fixture
def sync_ak_adapter():
    """同步版本的AkShareAdapter夹具"""
    return AkShareAdapter()


@pytest.fixture
def sync_sample_akshare_daily_data():
    """同步版本的模拟数据夹具"""
    return pd.DataFrame({
        '日期': ['2023-01-03', '2023-01-04', '2023-01-05'],
        '开盘': [10.0, 10.5, 11.0],
        '最高': [10.5, 11.0, 11.5],
        '最低': [9.9, 10.4, 10.9],
        '收盘': [10.3, 10.8, 11.2],
        '成交量': [1000000, 1200000, 1500000],
        '成交额': [10300000, 12960000, 16800000]
    })


@pytest.mark.asyncio
async def test_download_daily_success(ak_adapter, sync_sample_akshare_daily_data, monkeypatch):
    """测试成功下载日线数据"""
    # 使用同步函数模拟，避免协程未等待的问题
    def mock_stock_zh_a_hist(symbol, period, start_date, end_date, adjust):
        return sync_sample_akshare_daily_data
    
    # 模拟akshare.stock_zh_a_hist函数
    monkeypatch.setattr('akshare.stock_zh_a_hist', mock_stock_zh_a_hist)
    
    # 执行测试
    ts_code = '000001.SZ'
    start_date = '20230101'
    end_date = '20230105'
    result = await ak_adapter.download_daily(ts_code, start_date, end_date)
    
    # 简单验证结果
    assert isinstance(result, pd.DataFrame)
    assert not result.empty


@pytest.mark.asyncio
async def test_download_daily_with_adjust(ak_adapter, sync_sample_akshare_daily_data, monkeypatch):
    """测试下载日线数据并应用前复权"""
    # 使用同步函数模拟，避免协程未等待的问题
    def mock_stock_zh_a_hist(symbol, period, start_date, end_date, adjust):
        return sync_sample_akshare_daily_data
    
    monkeypatch.setattr('akshare.stock_zh_a_hist', mock_stock_zh_a_hist)
    
    # 执行测试
    ts_code = '000001.SZ'
    start_date = '20230101'
    end_date = '20230105'
    adjust_type = 'Forward'
    result = await ak_adapter.download_daily(ts_code, start_date, end_date, adjust_type)
    
    # 简单验证结果
    assert isinstance(result, pd.DataFrame)


@pytest.mark.asyncio
async def test_download_daily_empty_data(ak_adapter, monkeypatch):
    """测试下载空数据的情况"""
    # 使用同步函数模拟，避免协程未等待的问题
    def mock_stock_zh_a_hist(symbol, period, start_date, end_date, adjust):
        return pd.DataFrame()
    
    monkeypatch.setattr('akshare.stock_zh_a_hist', mock_stock_zh_a_hist)
    
    # 执行测试并验证异常
    ts_code = '000001.SZ'
    start_date = '20230101'
    end_date = '20230105'
    
    with pytest.raises(ValueError):
        await ak_adapter.download_daily(ts_code, start_date, end_date)


@pytest.mark.asyncio
async def test_download_daily_retry(ak_adapter, sync_sample_akshare_daily_data, monkeypatch):
    """测试下载失败重试机制"""
    # 使用计数器来跟踪调用次数
    call_count = 0
    
    def mock_stock_zh_a_hist(symbol, period, start_date, end_date, adjust):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise Exception("Test error")
        return sync_sample_akshare_daily_data
    
    # 定义异步sleep函数
    async def mock_sleep(x):
        return None
    
    monkeypatch.setattr('akshare.stock_zh_a_hist', mock_stock_zh_a_hist)
    # 模拟sleep函数避免延迟
    monkeypatch.setattr('asyncio.sleep', mock_sleep)
    
    # 执行测试
    ts_code = '000001.SZ'
    start_date = '20230101'
    end_date = '20230105'
    result = await ak_adapter.download_daily(ts_code, start_date, end_date)
    
    # 简单验证结果
    assert isinstance(result, pd.DataFrame)
    assert call_count >= 3  # 至少重试了3次


@pytest.mark.asyncio
async def test_download_daily_max_retries(ak_adapter, monkeypatch):
    """测试达到最大重试次数后抛出异常"""
    # 使用同步函数模拟，避免协程未等待的问题
    def mock_stock_zh_a_hist(symbol, period, start_date, end_date, adjust):
        raise Exception("Test error")
    
    # 定义异步sleep函数
    async def mock_sleep(x):
        return None
    
    monkeypatch.setattr('akshare.stock_zh_a_hist', mock_stock_zh_a_hist)
    # 模拟sleep函数避免延迟
    monkeypatch.setattr('asyncio.sleep', mock_sleep)
    
    # 执行测试并验证异常
    ts_code = '000001.SZ'
    start_date = '20230101'
    end_date = '20230105'
    
    with pytest.raises(Exception):
        await ak_adapter.download_daily(ts_code, start_date, end_date)


def test_to_ak_code_conversion(sync_ak_adapter):
    """测试股票代码转换功能"""
    # 测试深交所代码
    assert sync_ak_adapter._to_ak_code('000001.SZ') == '000001'
    assert sync_ak_adapter._to_ak_code('300001.SZ') == '300001'
    
    # 测试上交所代码
    assert sync_ak_adapter._to_ak_code('600000.SH') == '600000'
    assert sync_ak_adapter._to_ak_code('688001.SH') == '688001'
    
    # 测试已经是数字格式的代码
    assert sync_ak_adapter._to_ak_code('000001') == '000001'
    assert sync_ak_adapter._to_ak_code('600000') == '600000'


def test_format_stock_code(sync_ak_adapter):
    """测试格式化股票代码函数"""
    # 测试深市股票代码
    assert sync_ak_adapter._format_stock_code('000001') == '000001.SZ'
    assert sync_ak_adapter._format_stock_code('300000') == '300000.SZ'
    
    # 测试沪市股票代码
    assert sync_ak_adapter._format_stock_code('600000') == '600000.SH'
    assert sync_ak_adapter._format_stock_code('688001') == '688001.SH'


def test_get_source_info(sync_ak_adapter):
    """测试获取数据源信息功能"""
    source_info = sync_ak_adapter.get_source_info()
    
    # 验证必需的字段
    assert source_info['source_id'] == 'akshare'
    assert source_info['name'] == 'AkShare金融数据接口'
    assert source_info['is_active'] is True
    assert isinstance(source_info['supported_data_types'], list)
    assert len(source_info['supported_data_types']) > 0


@pytest.mark.asyncio
async def test_download_batch_concurrent(ak_adapter, sync_sample_akshare_daily_data, monkeypatch):
    """测试批量下载数据功能"""
    # 使用同步函数模拟，避免协程未等待的问题
    def mock_stock_zh_a_hist(symbol, period, start_date, end_date, adjust):
        return sync_sample_akshare_daily_data
    
    monkeypatch.setattr('akshare.stock_zh_a_hist', mock_stock_zh_a_hist)
    
    # 执行测试
    stock_pool = ['000001.SZ', '600000.SH']
    start_date = '20230101'
    end_date = '20230105'
    result = await ak_adapter.download_batch(stock_pool, start_date, end_date, max_concurrency=2)
    
    # 简单验证结果
    assert isinstance(result, dict)
    assert len(result) == 2
    assert '000001.SZ' in result
    assert '600000.SH' in result


@pytest.mark.asyncio
async def test_verify_data_availability(ak_adapter, monkeypatch):
    """测试验证数据可用性功能"""
    # 模拟download_daily方法
    async def mock_download_daily(ts_code, start_date, end_date, adjust_type=None):
        # 返回非空DataFrame表示数据可用
        data = {
            'trade_date': ['2023-01-03'],
            'open': [10.0],
            'high': [10.3],
            'low': [9.9],
            'close': [10.2],
            'vol': [1000000],
            'amount': [10200000],
            'adjust_flag': ['None']
        }
        return pd.DataFrame(data)
    
    # 替换实例方法
    ak_adapter.download_daily = mock_download_daily
    
    # 执行测试
    stock_codes = ['000001.SZ', '600000.SH']
    start_date = '20230101'
    end_date = '20230105'
    result = await ak_adapter.verify_data_availability(stock_codes, start_date, end_date)
    
    # 验证结果
    assert isinstance(result, dict)
    assert result['000001.SZ'] is True
    assert result['600000.SH'] is True


@pytest.mark.asyncio
async def test_verify_data_availability_empty_data(ak_adapter, monkeypatch):
    """测试验证数据可用性（空数据情况）"""
    # 模拟download_daily方法返回空数据
    async def mock_download_daily(ts_code, start_date, end_date, adjust_type=None):
        # 返回空DataFrame表示数据不可用
        return pd.DataFrame()
    
    # 替换实例方法
    ak_adapter.download_daily = mock_download_daily
    
    # 执行测试
    stock_codes = ['000001.SZ']
    start_date = '20230101'
    end_date = '20230105'
    result = await ak_adapter.verify_data_availability(stock_codes, start_date, end_date)
    
    # 验证结果
    assert result['000001.SZ'] is False


if __name__ == "__main__":
    pytest.main([__file__])
