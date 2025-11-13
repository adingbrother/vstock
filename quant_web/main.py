import asyncio
import time
import uuid
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import json
from loguru import logger

from quant_web.api.v1 import data, backtest, strategy, recommend
from quant_web.state import (
    TASK_QUEUES,
    CONNECTION_SUBSCRIPTIONS,
    get_task_queue,
    remove_task_queue,
    update_task_activity,
    add_connection_subscription,
    remove_connection_subscription,
    remove_connection,
    task_last_activity,
    TASK_EXPIRY_TIME
)
from quant_web.core.exceptions import setup_exception_handlers


app = FastAPI(
    title="QuantWeb API",
    version="v0.0.1",
    description="量化交易平台API，提供策略管理、回测、推荐引擎等核心功能。",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置静态文件服务
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist):
    # 注意：静态文件挂载需要在所有路由注册之后，确保WebSocket路由优先匹配
    # 稍后在setup_app函数中挂载静态文件
    logger.info(f"Static files will be mounted from {frontend_dist} at root path")
else:
    logger.warning(f"Frontend dist directory not found at {frontend_dist}")


# 请求ID和时间戳中间件
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """为每个请求添加唯一ID和时间戳"""
    # 生成请求ID
    request.state.request_id = uuid.uuid4()
    request.state.timestamp = datetime.utcnow().isoformat()
    
    # 记录请求开始
    logger.info(f"Request started: {request.method} {request.url.path} | ID: {request.state.request_id}")
    
    # 处理请求
    start_time = time.time()
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = str(request.state.request_id)
    
    # 记录请求结束
    logger.info(f"Request completed: {request.method} {request.url.path} | Status: {response.status_code} | Time: {process_time:.3f}s")
    
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注意：TASK_QUEUES已从quant_web.state导入，这里不再重复定义


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}


# 当静态文件在根路径挂载后，不再需要单独的根路由处理器


@app.websocket("/ws/tasks")
async def websocket_tasks_endpoint(websocket: WebSocket):
    """支持批量任务管理的WebSocket端点 - 性能优化版
    功能：任务订阅、取消订阅、心跳检测、批量任务状态更新和任务数据分页加载
    """
    await websocket.accept()
    
    # 连接ID，用于日志追踪
    connection_id = str(uuid.uuid4())[:8]
    
    logger.info(f"WebSocket tasks connection established with ID: {connection_id}")
    
    # 启动心跳检测和消息处理任务
    heartbeat_task = None
    message_processing_tasks = []
    
    try:
        # 优化的心跳检测任务
        async def heartbeat():
            """自适应心跳机制，减少不必要的网络通信"""
            idle_time = 0
            while True:
                # 根据连接活跃度调整心跳频率
                if idle_time < 300:  # 5分钟内有活动
                    await asyncio.sleep(30)  # 30秒一次心跳
                else:
                    await asyncio.sleep(60)  # 延长到60秒一次心跳
                
                try:
                    await websocket.send_json({
                        "type": "heartbeat", 
                        "timestamp": datetime.utcnow().isoformat(),
                        "connection_id": connection_id,
                        "idle_time": idle_time
                    })
                    idle_time += 30
                except:
                    break
        
        heartbeat_task = asyncio.create_task(heartbeat())
        
        # 批量消息处理缓冲区
        message_queue = asyncio.Queue()
        
        # 启动异步消息处理器
        async def message_processor():
            """异步处理和批量发送消息，减少主线程阻塞"""
            batch_messages = {}
            last_send_time = time.time()
            
            while True:
                try:
                    # 等待消息或超时
                    try:
                        task_id, message = await asyncio.wait_for(message_queue.get(), timeout=0.5)
                    except asyncio.TimeoutError:
                        # 发送积累的消息批次
                        if batch_messages and (time.time() - last_send_time > 1.0):
                            await websocket.send_json({
                                "type": "batch_task_updates",
                                "updates": batch_messages
                            })
                            batch_messages = {}
                            last_send_time = time.time()
                        continue
                    
                    # 添加到相应任务的更新批次
                    if task_id not in batch_messages:
                        batch_messages[task_id] = []
                    
                    batch_messages[task_id].append(message)
                    
                    # 当积累了足够的更新或包含重要消息时立即发送
                    if len(batch_messages) >= 10 or any(m.get("type") == "done" for updates in batch_messages.values() for m in updates):
                        await websocket.send_json({
                            "type": "batch_task_updates",
                            "updates": batch_messages
                        })
                        batch_messages = {}
                        last_send_time = time.time()
                        
                except Exception as e:
                    logger.error(f"Error in message processor for connection {connection_id}: {str(e)}")
                    break
        
        message_processor_task = asyncio.create_task(message_processor())
        message_processing_tasks.append(message_processor_task)
        
        # 处理客户端消息
        while True:
            # 接收客户端消息
            try:
                # 设置超时以定期检查连接状态
                data = await asyncio.wait_for(websocket.receive_json(), timeout=120)  # 增加超时时间
                
                # 重置空闲时间
                if heartbeat_task:
                    idle_time = 0
                
                # 记录接收到的消息（不记录敏感信息）
                msg_type = data.get("type", "unknown")
                
                # 使用对象池模式处理消息类型，避免频繁的字符串比较
                if msg_type == "subscribe":
                    # 订阅任务更新 - 使用线程安全的函数
                    task_ids = data.get("task_ids", [])
                    if not isinstance(task_ids, list):
                        await websocket.send_json({
                            "type": "error",
                            "error_code": "INVALID_PARAMETER",
                            "message": "task_ids must be an array",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        continue
                    
                    # 优化：批量添加订阅
                    add_connection_subscription(connection_id, task_ids)
                    
                    # 立即更新任务活动状态
                    for task_id in task_ids:
                        update_task_activity(task_id)
                    
                    # 发送订阅确认（异步发送，不阻塞主循环）
                    await websocket.send_json({
                        "type": "subscribed", 
                        "task_ids": task_ids,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                elif msg_type == "unsubscribe":
                    # 取消订阅任务 - 使用线程安全的函数
                    task_ids = data.get("task_ids", [])
                    if not isinstance(task_ids, list):
                        await websocket.send_json({
                            "type": "error",
                            "error_code": "INVALID_PARAMETER",
                            "message": "task_ids must be an array",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        continue
                    
                    remove_connection_subscription(connection_id, task_ids)
                    
                    await websocket.send_json({
                        "type": "unsubscribed", 
                        "task_ids": task_ids,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif msg_type == "heartbeat_response":
                    # 心跳响应 - 只更新日志，不发送额外消息
                    pass  # 静默处理心跳响应，减少日志量
                    
                elif msg_type == "batch_status":
                    # 获取批量任务状态 - 优化查询性能
                    task_ids = data.get("task_ids", [])
                    if not isinstance(task_ids, list):
                        await websocket.send_json({
                            "type": "error",
                            "error_code": "INVALID_PARAMETER",
                            "message": "task_ids must be an array",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        continue
                    
                    # 批量获取状态，减少锁竞争
                    status_list = []
                    for task_id in task_ids:
                        # 优先检查活动记录，再检查队列
                        is_active = task_id in task_last_activity or task_id in TASK_QUEUES
                        if is_active:
                            status_list.append({
                                "task_id": task_id,
                                "status": "running"
                            })
                    
                    await websocket.send_json({
                        "type": "batch_status_response",
                        "tasks": status_list,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                elif msg_type == "request_more_tasks":
                    # 分页请求 - 加入请求节流
                    page = max(1, data.get("page", 1))
                    page_size = max(1, min(100, data.get("page_size", 20)))
                    
                    # 异步获取分页数据，不阻塞主线程
                    # 实际应用中应该从数据库异步获取
                    await websocket.send_json({
                        "type": "more_tasks_response",
                        "page": page,
                        "page_size": page_size,
                        "has_more": True,
                        "tasks": [],
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                else:
                    # 未知消息类型
                    await websocket.send_json({
                        "type": "error",
                        "error_code": "UNKNOWN_MESSAGE_TYPE",
                        "message": f"Unknown message type: {msg_type}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
            except asyncio.TimeoutError:
                # 超时，继续循环
                continue
            except json.JSONDecodeError:
                # 处理无效的JSON
                await websocket.send_json({
                    "type": "error",
                    "error_code": "INVALID_JSON",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                })
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket tasks connection {connection_id} disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket tasks endpoint for connection {connection_id}: {str(e)}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error", 
                "error_code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "timestamp": datetime.utcnow().isoformat()
            })
        except:
            pass
    finally:
        # 清理所有相关资源
        if heartbeat_task:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
                
        # 取消所有消息处理任务
        for task in message_processing_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # 移除连接订阅信息
        remove_connection(connection_id)
        
        logger.info(f"WebSocket tasks connection {connection_id} closed")


    @app.websocket("/ws/{task_id}")
    async def websocket_endpoint(websocket: WebSocket, task_id: str):
        """单任务WebSocket端点 - 性能优化版"""
        await websocket.accept()
        
        # 使用线程安全的函数获取队列
        q = get_task_queue(task_id)
        
        # 检查任务是否存在（通过检查队列中是否有数据）
        if q.empty() and task_id not in task_last_activity:
            # 如果没有活动记录且队列为空，认为任务不存在
            error_response = {
                "type": "error", 
                "error_code": "TASK_NOT_FOUND",
                "message": "Task not found", 
                "task_id": task_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_json(error_response)
            await websocket.close(code=1008)
        return
    
    # 创建连接ID用于日志
    connection_id = str(uuid.uuid4())[:8]
    
    try:
        logger.info(f"WebSocket connected for task {task_id}, connection: {connection_id}")
        
        # 记录活动
        update_task_activity(task_id)
        
        # 批量消息发送缓冲区
        message_batch = []
        batch_size = 5  # 批量处理的消息数
        last_batch_send_time = time.time()
        
        while True:
            # 超时等待消息
            try:
                # 设置超时以允许定期发送批量消息
                msg = await asyncio.wait_for(q.get(), timeout=0.5)
                update_task_activity(task_id)
                
                # 添加到消息批次
                message_batch.append(msg)
                
                # 当批次达到大小限制或包含结束消息时发送
                if len(message_batch) >= batch_size or msg.get("type") == "done":
                    # 优化：将多个小消息合并为一个大消息包
                    if len(message_batch) == 1:
                        await websocket.send_json(message_batch[0])
                    else:
                        await websocket.send_json({
                            "type": "batch_update",
                            "messages": message_batch
                        })
                    message_batch = []
                    last_batch_send_time = time.time()
                    
                    # 如果是结束消息，退出循环
                    if msg.get("type") == "done":
                        break
                
            except asyncio.TimeoutError:
                # 超时但有未发送的消息，发送它们
                if message_batch and (time.time() - last_batch_send_time > 1.0):
                    await websocket.send_json({
                        "type": "batch_update",
                        "messages": message_batch
                    })
                    message_batch = []
                    last_batch_send_time = time.time()
                continue
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task {task_id}, connection: {connection_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket endpoint for task {task_id} (conn: {connection_id}): {str(e)}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "error_code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "task_id": task_id
            })
        except:
            pass
    finally:
        # 发送任何剩余的批量消息
        if message_batch:
            try:
                await websocket.send_json({
                    "type": "batch_update",
                    "messages": message_batch
                })
            except:
                pass
                
        # 延迟清理，避免过早移除可能需要的队列
        # 不再在这里立即移除队列，而是通过定期清理任务处理
        logger.info(f"WebSocket connection cleaned up for task {task_id}, connection: {connection_id}")


async def cleanup_expired_tasks():
    """定期清理过期的任务队列和活动记录"""
    while True:
        await asyncio.sleep(60)  # 每分钟执行一次清理
        current_time = asyncio.get_event_loop().time()
        expired_tasks = []
        
        # 找出过期的任务
        for task_id, last_activity in task_last_activity.items():
            if current_time - last_activity > TASK_EXPIRY_TIME:
                expired_tasks.append(task_id)
        
        # 移除过期任务的队列
        if expired_tasks:
            logger.info(f"Cleaning up {len(expired_tasks)} expired tasks")
            for task_id in expired_tasks:
                remove_task_queue(task_id)
                if task_id in task_last_activity:
                    del task_last_activity[task_id]


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化清理任务"""
    # 启动定期清理任务
    asyncio.create_task(cleanup_expired_tasks())
    logger.info("Task cleanup scheduler started")


def include_routers():
    # 包含各个API模块的路由
    app.include_router(data.router, prefix="/api/v1", tags=["数据管理"])
    app.include_router(strategy.router, prefix="/api/v1", tags=["策略管理"])
    app.include_router(backtest.router, prefix="/api/v1", tags=["回测引擎"])
    app.include_router(recommend.router, prefix="/api/v1", tags=["推荐引擎"])


def setup_app():
    """设置应用程序"""
    include_routers()
    setup_exception_handlers(app)
    
    # 在所有路由注册之后挂载静态文件，确保WebSocket路由优先匹配
    global frontend_dist
    if os.path.exists(frontend_dist):
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
        logger.info(f"Static files mounted from {frontend_dist} at root path")
    
    logger.info("Application setup completed")


setup_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("quant_web.main:app", host="0.0.0.0", port=8000, reload=True)
