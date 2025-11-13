import asyncio
import time
import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from datetime import datetime
from loguru import logger

from quant_web.state import TASK_QUEUES
from quant_web.core.tasks import start_download_simulation
from quant_web.tasks import download_stocks

router = APIRouter(
    prefix="/api/v1/data",
    tags=["数据管理"],
    responses={404: {"description": "Not found"}},
)


# 支持的数据源列表
SUPPORTED_SOURCES = ["akshare", "tushare", "baostock", "jqdata"]

# 模拟数据存储
data_cache: Dict[str, Dict] = {}
downloaded_stocks: Dict[str, List[str]] = {}


class DownloadRequest(BaseModel):
    """数据下载请求模型"""
    stock_list: List[str] = Field(..., example=["000001.SZ"], description="股票代码列表")
    start_date: str = Field(..., example="20230101", description="开始日期 (YYYYMMDD)")
    end_date: str = Field(..., example="20231231", description="结束日期 (YYYYMMDD)")
    source: str = Field("akshare", example="akshare", description="数据源")
    data_type: str = Field("daily", example="daily", description="数据类型 (daily/minute)")
    adjust_type: Optional[str] = Field("qfq", example="qfq", description="复权类型 (qfq/hfq/none)")
    
    @validator('stock_list')
    def validate_stock_list(cls, v):
        if not v or len(v) == 0:
            raise ValueError('股票列表不能为空')
        if len(v) > 100:
            raise ValueError('单次下载股票数量不能超过100只')
        return v
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y%m%d")
        except ValueError:
            raise ValueError('日期格式必须为YYYYMMDD')
        return v
    
    @validator('source')
    def validate_source(cls, v):
        if v not in SUPPORTED_SOURCES:
            raise ValueError(f'不支持的数据源，支持的数据源为: {SUPPORTED_SOURCES}')
        return v
    
    @validator('data_type')
    def validate_data_type(cls, v):
        if v not in ['daily', 'minute']:
            raise ValueError('数据类型必须为 daily 或 minute')
        return v
    
    @validator('adjust_type')
    def validate_adjust_type(cls, v):
        if v not in ['qfq', 'hfq', 'none']:
            raise ValueError('复权类型必须为 qfq、hfq 或 none')
        return v


class DownloadResponse(BaseModel):
    """数据下载响应模型"""
    task_id: str
    status: str
    estimated_seconds: int
    message: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    task_id: str
    status: str
    progress: float
    completed_count: int
    total_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class DataSourceInfo(BaseModel):
    """数据源信息模型"""
    name: str
    description: str
    available: bool
    supported_data_types: List[str]
    config_required: bool


class StockDataQuery(BaseModel):
    """股票数据查询模型"""
    stock_code: str = Field(..., example="000001.SZ", description="股票代码")
    start_date: Optional[str] = Field(None, example="20230101", description="开始日期 (YYYYMMDD)")
    end_date: Optional[str] = Field(None, example="20231231", description="结束日期 (YYYYMMDD)")
    fields: Optional[List[str]] = Field(None, example=["open", "high", "low", "close", "volume"], 
                                      description="需要返回的字段")
    limit: int = Field(1000, ge=1, le=10000, description="返回数据条数限制")


@router.post("/download", response_model=DownloadResponse, status_code=202)
async def download_data(req: DownloadRequest, background_tasks: BackgroundTasks):
    """
    下载股票数据
    
    - **stock_list**: 股票代码列表，单次最多100只
    - **start_date**: 开始日期 (YYYYMMDD)
    - **end_date**: 结束日期 (YYYYMMDD)
    - **source**: 数据源，支持 akshare、tushare、baostock、jqdata
    - **data_type**: 数据类型，daily 或 minute
    - **adjust_type**: 复权类型，qfq (前复权)、hfq (后复权) 或 none (不复权)
    """
    try:
        # 生成任务ID
        task_id = f"DL_{int(time.time() * 1000)}"
        
        # 创建内存队列用于WebSocket通知 (可选)
        q = asyncio.Queue()
        TASK_QUEUES[task_id] = q
        
        # 初始化任务状态
        task_status = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0.0,
            "completed_count": 0,
            "total_count": len(req.stock_list),
            "started_at": datetime.now(),
            "completed_at": None,
            "request": req.dict()
        }
        TASK_QUEUES[f"{task_id}_status"] = task_status
        
        # 尝试使用Celery任务队列
        try:
            download_stocks.delay(task_id, req.stock_list, req.start_date, req.end_date, 
                                 req.source, req.data_type, req.adjust_type)
            logger.info(f"使用Celery启动下载任务 {task_id} 用于 {len(req.stock_list)} 只股票")
        except Exception as e:
            # 如果Celery不可用，则使用本地模拟
            logger.warning(f"Celery不可用，使用本地模拟: {str(e)}")
            background_tasks.add_task(start_download_simulation, 
                                     task_id, req.stock_list, q, 
                                     req.start_date, req.end_date)
        
        # 估算完成时间（根据股票数量）
        estimated_seconds = max(5, len(req.stock_list) * 2)
        
        return DownloadResponse(
            task_id=task_id,
            status="pending",
            estimated_seconds=estimated_seconds,
            message=f"开始下载 {len(req.stock_list)} 只股票的数据"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建下载任务失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"code": 50001, "message": f"创建下载任务失败: {str(e)}"}
        )


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    获取下载任务状态
    
    - **task_id**: 任务ID
    """
    try:
        # 从内存中获取任务状态
        task_status = TASK_QUEUES.get(f"{task_id}_status")
        
        if not task_status:
            # 模拟任务状态（在实际应用中，应该从数据库或缓存中获取）
            if not task_id.startswith("DL_"):
                raise HTTPException(status_code=404, detail={"code": 40401, "message": "任务不存在"})
            
            # 模拟任务状态
            task_status = {
                "task_id": task_id,
                "status": "completed",
                "progress": 100.0,
                "completed_count": 5,  # 模拟值
                "total_count": 5,
                "started_at": datetime.now(),
                "completed_at": datetime.now()
            }
        
        return TaskStatusResponse(**task_status)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"code": 50002, "message": "获取任务状态失败"}
        )


@router.get("/sources", response_model=List[DataSourceInfo])
async def get_data_sources():
    """
    获取支持的数据源列表
    """
    try:
        # 在实际应用中，这里应该检查每个数据源的可用性
        sources_info = [
            {
                "name": "akshare",
                "description": "开源的财经数据接口库",
                "available": True,
                "supported_data_types": ["daily", "minute", "index", "fund"],
                "config_required": False
            },
            {
                "name": "tushare",
                "description": "金融大数据平台",
                "available": False,  # 模拟不可用
                "supported_data_types": ["daily", "minute", "index", "fund", "futures"],
                "config_required": True
            },
            {
                "name": "baostock",
                "description": "baostock金融数据平台",
                "available": True,
                "supported_data_types": ["daily", "index"],
                "config_required": False
            },
            {
                "name": "jqdata",
                "description": "聚宽数据平台",
                "available": False,  # 模拟不可用
                "supported_data_types": ["daily", "minute", "index", "fund", "options"],
                "config_required": True
            }
        ]
        
        return [DataSourceInfo(**source) for source in sources_info]
    except Exception as e:
        logger.error(f"获取数据源列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"code": 50003, "message": "获取数据源列表失败"}
        )


@router.get("/stocks")
async def get_downloaded_stocks(
    source: Optional[str] = Query(None, description="数据源"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
) -> Dict[str, Any]:
    """
    获取已下载的股票列表
    
    - **source**: 可选的数据源过滤
    - **limit**: 返回数量限制
    - **offset**: 偏移量（分页）
    """
    try:
        # 在实际应用中，这里应该从数据库中查询
        # 模拟已下载的股票数据
        if not downloaded_stocks:
            # 初始化模拟数据
            downloaded_stocks["akshare"] = ["000001.SZ", "000002.SZ", "600000.SH", "600036.SH", "000858.SZ", 
                                           "002594.SZ", "300750.SZ", "601318.SH", "600519.SH", "000063.SZ"]
            downloaded_stocks["baostock"] = ["000001.SZ", "000002.SZ", "600000.SH"]
        
        # 过滤数据源
        if source:
            if source not in downloaded_stocks:
                return {"total": 0, "stocks": []}
            stocks = downloaded_stocks[source]
        else:
            # 合并所有数据源的股票列表，去重
            all_stocks = set()
            for s_list in downloaded_stocks.values():
                all_stocks.update(s_list)
            stocks = list(all_stocks)
            stocks.sort()
        
        # 计算总数和分页
        total = len(stocks)
        paged_stocks = stocks[offset:offset + limit]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "stocks": paged_stocks,
            "has_more": offset + limit < total
        }
    except Exception as e:
        logger.error(f"获取已下载股票列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"code": 50004, "message": "获取已下载股票列表失败"}
        )


@router.post("/query")
async def query_stock_data(query: StockDataQuery) -> Dict[str, Any]:
    """
    查询股票数据
    
    - **stock_code**: 股票代码
    - **start_date**: 可选的开始日期 (YYYYMMDD)
    - **end_date**: 可选的结束日期 (YYYYMMDD)
    - **fields**: 可选的需要返回的字段列表
    - **limit**: 返回数据条数限制
    """
    try:
        # 在实际应用中，这里应该从数据库或文件系统中读取数据
        # 模拟股票数据查询
        if query.stock_code not in data_cache:
            # 生成模拟数据
            generate_mock_stock_data(query.stock_code)
        
        stock_data = data_cache[query.stock_code]
        
        # 过滤字段
        if query.fields:
            filtered_data = []
            for record in stock_data["data"]:
                filtered_record = {k: v for k, v in record.items() if k in query.fields or k == "date"}
                filtered_data.append(filtered_record)
            stock_data["data"] = filtered_data
        
        # 限制返回数量
        limited_data = stock_data["data"][:query.limit]
        
        return {
            "stock_code": query.stock_code,
            "total": len(stock_data["data"]),
            "returned": len(limited_data),
            "data": limited_data,
            "source": stock_data["source"],
            "last_update": stock_data["last_update"]
        }
    except Exception as e:
        logger.error(f"查询股票数据失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"code": 50005, "message": "查询股票数据失败"}
        )


@router.delete("/stocks/{stock_code}")
async def delete_stock_data(stock_code: str) -> Dict[str, Any]:
    """
    删除指定股票的数据
    
    - **stock_code**: 股票代码
    """
    try:
        # 在实际应用中，这里应该从数据库或文件系统中删除数据
        if stock_code in data_cache:
            del data_cache[stock_code]
            
        # 从下载列表中移除
        for source, stocks in downloaded_stocks.items():
            if stock_code in stocks:
                stocks.remove(stock_code)
        
        return {"message": f"股票 {stock_code} 的数据已成功删除"}
    except Exception as e:
        logger.error(f"删除股票数据失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"code": 50006, "message": "删除股票数据失败"}
        )


@router.get("/cache/info")
async def get_cache_info() -> Dict[str, Any]:
    """
    获取缓存信息
    """
    try:
        # 在实际应用中，这里应该计算实际的缓存大小和使用情况
        cache_size = sum(len(str(data)) for data in data_cache.values()) / (1024 * 1024)  # MB
        
        return {
            "cached_stocks_count": len(data_cache),
            "estimated_size_mb": round(cache_size, 2),
            "available_memory_mb": 8192,  # 模拟值
            "cache_hit_rate": 0.75,  # 模拟值
            "last_cache_cleanup": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取缓存信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"code": 50007, "message": "获取缓存信息失败"}
        )


@router.post("/cache/clear")
async def clear_cache() -> Dict[str, Any]:
    """
    清空缓存
    """
    try:
        # 清空缓存
        cleared_count = len(data_cache)
        data_cache.clear()
        
        logger.info(f"已清空 {cleared_count} 只股票的数据缓存")
        return {"message": f"缓存已清空，共清除 {cleared_count} 只股票的数据"}
    except Exception as e:
        logger.error(f"清空缓存失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"code": 50008, "message": "清空缓存失败"}
        )


# 辅助函数
def generate_mock_stock_data(stock_code: str) -> None:
    """生成模拟股票数据"""
    import random
    
    # 生成30天的模拟数据
    data = []
    base_price = random.uniform(10, 100)
    
    for i in range(30):
        date = (datetime.now() - timedelta(days=29-i)).strftime("%Y%m%d")
        change = random.uniform(-0.05, 0.05)
        base_price = base_price * (1 + change)
        
        record = {
            "date": date,
            "open": round(base_price * random.uniform(0.98, 1.02), 2),
            "high": round(base_price * random.uniform(1.0, 1.03), 2),
            "low": round(base_price * random.uniform(0.97, 1.0), 2),
            "close": round(base_price, 2),
            "volume": int(random.uniform(100000, 10000000)),
            "amount": round(random.uniform(1000000, 100000000), 2),
            "pct_change": round(change * 100, 2)
        }
        data.append(record)
    
    # 按日期排序（升序）
    data.sort(key=lambda x: x["date"])
    
    data_cache[stock_code] = {
        "data": data,
        "source": "akshare",
        "last_update": datetime.now().isoformat()
    }


# 添加缺失的导入
from datetime import timedelta
