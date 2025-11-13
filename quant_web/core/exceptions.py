from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from loguru import logger


class QuantWebError(Exception):
    """系统基础异常类"""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", status_code: int = 500, 
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DataError(QuantWebError):
    """数据相关错误"""
    
    def __init__(self, message: str, error_code: str = "DATA_ERROR", 
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, status_code=400, details=details)


class ValidationError(DataError):
    """数据验证错误"""
    
    def __init__(self, message: str, validation_errors: Optional[Dict[str, str]] = None):
        details = {"validation_errors": validation_errors} if validation_errors else {}
        super().__init__(message, "VALIDATION_ERROR", details=details)


class NotFoundError(QuantWebError):
    """资源未找到错误"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        super().__init__(message, "NOT_FOUND", status_code=404, details=details)


class TaskError(QuantWebError):
    """任务相关错误"""
    
    def __init__(self, message: str, task_id: Optional[str] = None, task_type: Optional[str] = None):
        details = {}
        if task_id:
            details["task_id"] = task_id
        if task_type:
            details["task_type"] = task_type
        super().__init__(message, "TASK_ERROR", status_code=500, details=details)


class BacktestError(TaskError):
    """回测相关错误"""
    
    def __init__(self, message: str, strategy_id: Optional[str] = None, backtest_id: Optional[str] = None):
        details = {}
        if strategy_id:
            details["strategy_id"] = strategy_id
        if backtest_id:
            details["backtest_id"] = backtest_id
        super().__init__(message, task_id=backtest_id, task_type="backtest", details=details)


class StrategyError(BacktestError):
    """策略相关错误"""
    
    def __init__(self, message: str, strategy_id: Optional[str] = None, strategy_name: Optional[str] = None):
        details = {}
        if strategy_name:
            details["strategy_name"] = strategy_name
        super().__init__(message, strategy_id=strategy_id, details=details)
        self.error_code = "STRATEGY_ERROR"


class OrderError(BacktestError):
    """订单相关错误"""
    
    def __init__(self, message: str, order_id: Optional[str] = None, strategy_id: Optional[str] = None):
        details = {}
        if order_id:
            details["order_id"] = order_id
        super().__init__(message, strategy_id=strategy_id, details=details)
        self.error_code = "ORDER_ERROR"


class PortfolioError(BacktestError):
    """投资组合相关错误"""
    
    def __init__(self, message: str, portfolio_id: Optional[str] = None, strategy_id: Optional[str] = None):
        details = {}
        if portfolio_id:
            details["portfolio_id"] = portfolio_id
        super().__init__(message, strategy_id=strategy_id, details=details)
        self.error_code = "PORTFOLIO_ERROR"


class BacktestTimeoutError(BacktestError):
    """回测超时错误"""
    
    def __init__(self, message: str, timeout_seconds: Optional[int] = None, strategy_id: Optional[str] = None):
        details = {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        super().__init__(message, strategy_id=strategy_id, details=details)
        self.error_code = "BACKTEST_TIMEOUT"
        self.status_code = 408  # Request Timeout


class APIError(QuantWebError):
    """API调用错误"""
    
    def __init__(self, message: str, endpoint: Optional[str] = None, params: Optional[Dict[str, Any]] = None):
        details = {}
        if endpoint:
            details["endpoint"] = endpoint
        if params:
            details["params"] = params
        super().__init__(message, "API_ERROR", status_code=502, details=details)


class DatabaseError(QuantWebError):
    """数据库相关错误"""
    
    def __init__(self, message: str, operation: Optional[str] = None, table: Optional[str] = None):
        details = {}
        if operation:
            details["operation"] = operation
        if table:
            details["table"] = table
        super().__init__(message, "DATABASE_ERROR", status_code=500, details=details)


class DatabaseConnectionError(DatabaseError):
    """数据库连接错误"""
    
    def __init__(self, message: str, host: Optional[str] = None, port: Optional[int] = None):
        details = {}
        if host:
            details["host"] = host
        if port:
            details["port"] = port
        super().__init__(message, operation="connection", details=details)
        self.error_code = "DATABASE_CONNECTION_ERROR"


class DatabaseQueryError(DatabaseError):
    """数据库查询错误"""
    
    def __init__(self, message: str, query: Optional[str] = None, table: Optional[str] = None):
        details = {}
        if query:
            details["query"] = query[:500]  # 限制查询字符串长度
        super().__init__(message, operation="query", table=table, details=details)
        self.error_code = "DATABASE_QUERY_ERROR"


class DatabaseTransactionError(DatabaseError):
    """数据库事务错误"""
    
    def __init__(self, message: str, transaction_id: Optional[str] = None):
        details = {}
        if transaction_id:
            details["transaction_id"] = transaction_id
        super().__init__(message, operation="transaction", details=details)
        self.error_code = "DATABASE_TRANSACTION_ERROR"


class WebSocketError(QuantWebError):
    """WebSocket相关错误"""
    
    def __init__(self, message: str, connection_id: Optional[str] = None, action: Optional[str] = None):
        details = {}
        if connection_id:
            details["connection_id"] = connection_id
        if action:
            details["action"] = action
        super().__init__(message, "WEBSOCKET_ERROR", status_code=1008, details=details)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """增强的全局异常处理器，提供一致的错误格式和详细的错误信息"""
    
    # 获取请求上下文信息
    request_id = str(getattr(request.state, "request_id", "unknown"))
    timestamp = getattr(request.state, "timestamp", datetime.utcnow().isoformat())
    path = getattr(request, "url", {}).path if hasattr(request, "url") else "unknown"
    method = getattr(request, "method", "unknown")
    
    # 记录异常详情，包含请求上下文
    logger.error(
        f"Global exception caught: {exc} | Request: {method} {path} | ID: {request_id}",
        exc_info=True
    )
    
    # 统一的错误响应结构
    error_response = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {}
        },
        "request_id": request_id,
        "timestamp": timestamp,
        "path": path,
        "method": method
    }
    
    # 处理自定义异常
    if isinstance(exc, QuantWebError):
        error_response["error"]["code"] = exc.error_code
        error_response["error"]["message"] = exc.message
        error_response["error"]["details"] = exc.details
        status_code = exc.status_code
        
        # 针对数据库错误提供额外信息
        if isinstance(exc, DatabaseError):
            logger.critical(
                f"Database error occurred during {method} {path}: {exc.error_code} - {exc.message}",
                exc_info=True
            )
            
        # 针对API错误提供额外信息
        elif isinstance(exc, APIError):
            logger.error(
                f"API error occurred during {method} {path}: {exc.error_code} - {exc.message}",
                exc_info=True
            )
    
    # 处理FastAPI的HTTPException
    elif isinstance(exc, HTTPException):
        error_response["error"]["code"] = f"HTTP_{exc.status_code}"
        error_response["error"]["message"] = exc.detail
        status_code = exc.status_code
    
    # 处理Python标准异常
    elif isinstance(exc, ValueError):
        error_response["error"]["code"] = "VALUE_ERROR"
        error_response["error"]["message"] = str(exc)
        error_response["error"]["details"]["exception_type"] = "ValueError"
        status_code = status.HTTP_400_BAD_REQUEST
    
    elif isinstance(exc, TypeError):
        error_response["error"]["code"] = "TYPE_ERROR"
        error_response["error"]["message"] = f"Type error: {str(exc)}"
        error_response["error"]["details"]["exception_type"] = "TypeError"
        status_code = status.HTTP_400_BAD_REQUEST
    
    elif isinstance(exc, KeyError):
        error_response["error"]["code"] = "KEY_ERROR"
        error_response["error"]["message"] = f"Missing required key: {str(exc)}"
        error_response["error"]["details"]["exception_type"] = "KeyError"
        status_code = status.HTTP_400_BAD_REQUEST
    
    # 处理其他未预期的异常
    else:
        # 在开发环境中可以包含更多详细信息
        import os
        if os.environ.get("ENVIRONMENT", "production").lower() != "production":
            error_response["error"]["details"]["exception_type"] = type(exc).__name__
            error_response["error"]["details"]["exception_message"] = str(exc)
        
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # 记录将要发送的错误响应（不记录敏感信息）
    sanitized_response = error_response.copy()
    if "params" in sanitized_response["error"]["details"]:
        sanitized_response["error"]["details"]["params"] = "<sanitized>"
    logger.debug(f"Sending error response: {sanitized_response}")
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


def setup_exception_handlers(app):
    """设置异常处理器"""
    app.add_exception_handler(Exception, global_exception_handler)
    logger.info("Exception handlers configured")
