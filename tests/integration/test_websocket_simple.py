import pytest
import asyncio
from fastapi.testclient import TestClient
from quant_web.main import app
from quant_web.core.task_manager import TaskStatus
from quant_web.state import TASK_QUEUES

client = TestClient(app)

class SimpleTestTask:
    """简化的测试任务类"""
    def __init__(self, task_id):
        self.task_id = task_id
        self.status = TaskStatus.PENDING
    
    async def execute(self):
        """执行简单任务"""
        if self.task_id not in TASK_QUEUES:
            TASK_QUEUES[self.task_id] = asyncio.Queue()
        
        # 发送开始消息
        await TASK_QUEUES[self.task_id].put({
            "type": "start",
            "task_id": self.task_id,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # 模拟完成
        await TASK_QUEUES[self.task_id].put({
            "type": "done",
            "task_id": self.task_id,
            "result": {"success": True}
        })

@pytest.mark.asyncio
async def test_websocket_simple_connection():
    """测试基本的WebSocket连接功能"""
    # 清理环境
    test_task_id = "simple-test-task"
    if test_task_id in TASK_QUEUES:
        del TASK_QUEUES[test_task_id]
    
    try:
        # 创建测试任务
        test_task = SimpleTestTask(test_task_id)
        
        # 使用正确的方式连接WebSocket
        websocket = client.websocket_connect("/ws/tasks")
        
        try:
            # 发送订阅消息
            websocket.send_json({
                "type": "subscribe",
                "task_ids": [test_task_id]
            })
            
            # 验证订阅成功响应
            response = websocket.receive_json()
            assert response["type"] == "subscribed"
            assert test_task_id in response["task_ids"]
            
        finally:
            # 关闭连接
            websocket.close()
            
    finally:
        # 清理
        if test_task_id in TASK_QUEUES:
            del TASK_QUEUES[test_task_id]

if __name__ == "__main__":
    pytest.main([__file__])