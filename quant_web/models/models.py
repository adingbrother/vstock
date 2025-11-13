from sqlalchemy import Column, String, Integer, Text, Float, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.dialects.sqlite import JSON

from models.database import Base


class StockBasic(Base):
    __tablename__ = 'stock_basic'
    ts_code = Column(String, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    name = Column(String, nullable=False)
    area = Column(String)
    industry = Column(String)
    list_date = Column(String)
    data_source = Column(String, default='akshare')
    status = Column(Integer, default=1)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())


class Strategy(Base):
    __tablename__ = 'strategy'
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    code = Column(Text, nullable=False)
    params_json = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    version = Column(Integer, default=1)


class Task(Base):
    __tablename__ = 'task'
    id = Column(String, primary_key=True)
    task_type = Column(String, nullable=False, index=True)
    priority = Column(String, default='medium')
    status = Column(String, nullable=False, default='pending', index=True)
    progress = Column(Float, default=0.0)
    parameters = Column(Text)  # JSON string for task parameters
    result = Column(Text)  # JSON string for task result
    error_message = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)


class BacktestTask(Base):
    __tablename__ = 'backtest_task'
    id = Column(String, primary_key=True)
    strategy_id = Column(String)
    stock_pool = Column(Text)  # JSON array as string
    start_date = Column(String)
    end_date = Column(String)
    init_cash = Column(Float)
    status = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    report_path = Column(String)


class RecommendResult(Base):
    __tablename__ = 'recommend_result'
    id = Column(String, primary_key=True)
    task_id = Column(String)
    trade_date = Column(String)
    rank = Column(Integer)
    ts_code = Column(String)
    score = Column(Float)
    reason = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())


class DataDownloadLog(Base):
    __tablename__ = 'data_download_log'
    id = Column(String, primary_key=True)
    task_id = Column(String, index=True)
    ts_code = Column(String)
    status = Column(String)
    message = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
