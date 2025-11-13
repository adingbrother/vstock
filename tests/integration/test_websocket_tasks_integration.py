import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from quant_web.main import app
from quant_web.core.task_manager import TaskStatus, TaskFactory
from quant_web.state import TASK_QUEUES, GLOBAL_TASK_CACHE
from quant_web.core.exceptions import QuantWebError

client = TestClient(app)


class IntegrationTestTask:
    """用于集成测试的简单任务类"""
    def __init__(self, task_id, task_type="test"):
        self.task_id = task_id
        self.task_type = task_type
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.name = f"Test Task {task_id}"
        self.created_at = asyncio.get_event_loop().time()
    
    async def execute_and_notify(self):
        """执行任务并通过队列发送通知"""
        if self.task_id not in TASK_QUEUES:
            TASK_QUEUES[self.task_id] = asyncio.Queue()
        
        try:
            # 发送开始消息
            await TASK_QUEUES[self.task_id].put({
                "type": "start",
                "task_id": self.task_id,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            # 模拟进度更新
            for progress in [25, 50, 75, 100]:
                self.progress = progress
                await TASK_QUEUES[self.task_id].put({
                    "type": "progress",
                    "task_id": self.task_id,
                    "progress": progress,
                    "message": f"Progress: {progress}%"
                })
                await asyncio.sleep(0.1)
            
            # 发送完成消息
            self.status = TaskStatus.COMPLETED
            await TASK_QUEUES[self.task_id].put({
                "type": "done",
                "task_id": self.task_id,
                "result": {"success": True},
                "timestamp": asyncio.get_event_loop().time()
            })
            
        except Exception as e:
            # 发送错误消息
            self.status = TaskStatus.FAILED
            await TASK_QUEUES[self.task_id].put({
                "type": "error",
                "task_id": self.task_id,
                "error": str(e),
                "error_code": 50001,
                "timestamp": asyncio.get_event_loop().time()
            })


def mock_get_tasks(page, page_size):
    """模拟获取分页任务的函数"""
    # 创建模拟任务列表
    total_tasks = 30
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_tasks)
    
    tasks = []
    for i in range(start_idx, end_idx):
        task_id = f"mock-task-{i + 1}"
        status = [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.FAILED][i % 4]
        tasks.append({
            "task_id": task_id,
            "status": status,
            "progress": 0 if status == TaskStatus.PENDING else 100 if status == TaskStatus.COMPLETED else 50,
            "name": f"Mock Task {i + 1}",
            "task_type": "download" if i % 2 == 0 else "backtest",
            "created_at": f"2024-01-{i % 30 + 1:02d}T12:00:00Z"
        })
    
    return tasks, end_idx < total_tasks


@pytest.mark.asyncio
async def test_websocket_tasks_integration():
    """集成测试：测试WebSocket与任务管理的协同工作"""
    task_id = "integration-test-task-1"
    
    # 创建测试任务并在后台执行
    test_task = IntegrationTestTask(task_id)
    task_execution = asyncio.create_task(test_task.execute_and_notify())
    
    try:
        # 连接到WebSocket tasks端点
        async with client.websocket_connect("/ws/tasks") as websocket:
            # 订阅任务
            await websocket.send_json({
                "type": "subscribe",
                "task_ids": [task_id]
            })
            
            # 验证订阅成功
            response = await websocket.receive_json()
            assert response["type"] == "subscribed"
            assert task_id in response["task_ids"]
            
            # 查询批量状态
            await websocket.send_json({
                "type": "batch_status",
                "task_ids": [task_id]
            })
            
            # 验证批量状态响应
            status_response = await websocket.receive_json()
            assert status_response["type"] == "batch_status_response"
            # 由于我们创建了队列，任务应该显示为running
            running_tasks = [t for t in status_response["tasks"] if t["task_id"] == task_id]
            assert len(running_tasks) == 1
            assert running_tasks[0]["status"] == "running"
            
    finally:
        # 等待任务完成或取消
        try:
            await asyncio.wait_for(task_execution, timeout=2.0)
        except asyncio.TimeoutError:
            task_execution.cancel()
        
        # 清理任务队列
        if task_id in TASK_QUEUES:
            del TASK_QUEUES[task_id]


@pytest.mark.asyncio
async def test_websocket_request_more_tasks():
    """测试request_more_tasks功能"""
    # 保存原始的get_tasks方法
    from quant_web.core.task_manager import get_tasks
    original_get_tasks = get_tasks
    
    # 替换为模拟方法
    from quant_web.core import task_manager
    task_manager.get_tasks = mock_get_tasks
    
    try:
        async with client.websocket_connect("/ws/tasks") as websocket:
            # 请求第一页任务
            await websocket.send_json({
                "type": "request_more_tasks",
                "page": 1,
                "page_size": 10
            })
            
            # 验证响应
            response = await websocket.receive_json()
            assert response["type"] == "tasks_batch"
            assert len(response["tasks"]) == 10
            assert response["has_more"] is True
            assert response["page"] == 1
            
            # 请求第二页任务
            await websocket.send_json({
                "type": "request_more_tasks",
                "page": 2,
                "page_size": 10
            })
            
            # 验证第二页响应
            response2 = await websocket.receive_json()
            assert response2["type"] == "tasks_batch"
            assert len(response2["tasks"]) == 10
            assert response2["has_more"] is True
            assert response2["page"] == 2
            
            # 请求最后一页任务
            await websocket.send_json({
                "type": "request_more_tasks",
                "page": 3,
                "page_size": 10
            })
            
            # 验证最后一页响应
            response3 = await websocket.receive_json()
            assert response3["type"] == "tasks_batch"
            assert len(response3["tasks"]) == 10
            assert response3["has_more"] is False
            assert response3["page"] == 3
            
    finally:
        # 恢复原始方法
        task_manager.get_tasks = original_get_tasks


@pytest.mark.asyncio
async def test_websocket_error_handling():
    """测试WebSocket错误处理"""
    async with client.websocket_connect("/ws/tasks") as websocket:
        # 发送无效消息格式
        await websocket.send_json({"invalid": "format"})
        
        # 验证错误响应
        error_response = await websocket.receive_json()
        assert error_response["type"] == "error"
        assert "error_code" in error_response
        assert "message" in error_response
        assert "timestamp" in error_response
        
        # 发送缺少必要参数的消息
        await websocket.send_json({
            "type": "request_more_tasks"
        })
        
        # 验证参数错误响应
        param_error_response = await websocket.receive_json()
        assert param_error_response["type"] == "error"
        assert param_error_response["error_code"] == 400
        assert "参数错误" in param_error_response["message"]


@pytest.mark.asyncio
async def test_websocket_unsubscribe():
    """测试取消订阅功能"""
    task_id = "subscribe-test-task"
    
    # 创建任务队列
    TASK_QUEUES[task_id] = asyncio.Queue()
    
    try:
        async with client.websocket_connect("/ws/tasks") as websocket:
            # 订阅任务
            await websocket.send_json({
                "type": "subscribe",
                "task_ids": [task_id]
            })
            
            # 验证订阅成功
            subscribe_response = await websocket.receive_json()
            assert subscribe_response["type"] == "subscribed"
            assert task_id in subscribe_response["task_ids"]
            
            # 取消订阅
            await websocket.send_json({
                "type": "unsubscribe",
                "task_ids": [task_id]
            })
            
            # 验证取消订阅成功
            unsubscribe_response = await websocket.receive_json()
            assert unsubscribe_response["type"] == "unsubscribed"
            assert task_id in unsubscribe_response["task_ids"]
            
    finally:
        # 清理
        if task_id in TASK_QUEUES:
            del TASK_QUEUES[task_id]


@pytest.mark.asyncio
async def test_multiple_websocket_connections():
    """测试多个WebSocket连接同时订阅相同任务"""
    task_id = "multi-connect-test-task"
    
    # 创建测试任务
    test_task = IntegrationTestTask(task_id)
    
    # 启动任务执行
    task_execution = asyncio.create_task(test_task.execute_and_notify())
    
    try:
        # 创建两个WebSocket连接
        conn1 = client.websocket_connect("/ws/tasks")
        conn2 = client.websocket_connect("/ws/tasks")
        
        async with conn1 as ws1, conn2 as ws2:
            # 两个连接都订阅同一个任务
            await ws1.send_json({
                "type": "subscribe",
                "task_ids": [task_id]
            })
            await ws2.send_json({
                "type": "subscribe",
                "task_ids": [task_id]
            })
            
            # 验证两个连接都收到订阅成功响应
            resp1 = await ws1.receive_json()
            resp2 = await ws2.receive_json()
            
            assert resp1["type"] == "subscribed"
            assert resp2["type"] == "subscribed"
            assert task_id in resp1["task_ids"]
            assert task_id in resp2["task_ids"]
            
            # 等待任务进度更新，两个连接都应该收到
            progress_received1 = False
            progress_received2 = False
            
            # 设置超时
            timeout = asyncio.get_event_loop().time() + 3.0
            
            # 尝试接收进度更新消息
            while not (progress_received1 and progress_received2) and asyncio.get_event_loop().time() < timeout:
                try:
                    # 非阻塞接收，设置短超时
                    msg1 = await asyncio.wait_for(ws1.receive_json(), timeout=0.5)
                    if msg1["type"] == "progress" and msg1["task_id"] == task_id:
                        progress_received1 = True
                except asyncio.TimeoutError:
                    pass
                
                try:
                    msg2 = await asyncio.wait_for(ws2.receive_json(), timeout=0.5)
                    if msg2["type"] == "progress" and msg2["task_id"] == task_id:
                        progress_received2 = True
                except asyncio.TimeoutError:
                    pass
            
            # 验证两个连接都收到了进度更新
            assert progress_received1, "连接1未收到进度更新"
            assert progress_received2, "连接2未收到进度更新"
            
    finally:
        # 等待任务完成或取消
        try:
            await asyncio.wait_for(task_execution, timeout=2.0)
        except asyncio.TimeoutError:
            task_execution.cancel()
        
        # 清理
        if task_id in TASK_QUEUES:
            del TASK_QUEUES[task_id]

if __name__ == "__main__":
    pytest.main([__file__])
