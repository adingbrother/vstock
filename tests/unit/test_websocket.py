import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
import asyncio
import json
from quant_web.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_websocket_tasks_endpoint_subscribe():
    """测试WebSocket tasks端点的订阅功能"""
    async with client.websocket_connect("/ws/tasks") as websocket:
        # 测试订阅消息
        subscribe_msg = {
            "type": "subscribe",
            "task_ids": ["test-task-1", "test-task-2"]
        }
        await websocket.send_json(subscribe_msg)
        
        # 接收订阅响应
        response = await websocket.receive_json()
        assert response["type"] == "subscribed"
        assert set(response["task_ids"]) == {"test-task-1", "test-task-2"}
        assert "Successfully subscribed" in response["message"]
        
        # 测试心跳响应
        try:
            # 等待心跳消息
            response = await asyncio.wait_for(websocket.receive_json(), timeout=5)
            if response["type"] == "heartbeat":
                # 发送心跳响应
                await websocket.send_json({"type": "heartbeat_response"})
        except asyncio.TimeoutError:
            # 5秒内没有收到心跳是正常的，因为心跳间隔是30秒
            pass
        
        # 测试取消订阅
        unsubscribe_msg = {
            "type": "unsubscribe",
            "task_ids": ["test-task-1"]
        }
        await websocket.send_json(unsubscribe_msg)
        
        # 接收取消订阅响应
        response = await websocket.receive_json()
        assert response["type"] == "unsubscribed"
        assert set(response["task_ids"]) == {"test-task-2"}
        assert "Successfully unsubscribed" in response["message"]
        
        # 测试未知消息类型
        unknown_msg = {
            "type": "unknown_command",
            "data": "test"
        }
        await websocket.send_json(unknown_msg)
        
        # 接收错误响应
        response = await websocket.receive_json()
        assert response["type"] == "error"
        assert "Unknown message type" in response["message"]


@pytest.mark.asyncio
async def test_websocket_tasks_endpoint_batch_status():
    """测试WebSocket tasks端点的批量状态查询功能"""
    async with client.websocket_connect("/ws/tasks") as websocket:
        # 测试批量状态查询
        batch_status_msg = {
            "type": "batch_status",
            "task_ids": ["test-task-1", "test-task-2"]
        }
        await websocket.send_json(batch_status_msg)
        
        # 接收批量状态响应
        response = await websocket.receive_json()
        assert response["type"] == "batch_status_response"
        assert isinstance(response["tasks"], list)
        # 由于我们没有实际创建这些任务，响应列表应该为空或只包含运行中的任务


@pytest.mark.asyncio
async def test_websocket_single_task_endpoint():
    """测试单个任务的WebSocket端点"""
    # 测试不存在的任务
    with pytest.raises(WebSocketDisconnect):
        async with client.websocket_connect("/ws/nonexistent-task-123") as websocket:
            # 应该收到错误消息然后断开连接
            response = await websocket.receive_json()
            assert response["type"] == "error"
            assert "task not found" in response["message"]
            # 连接会在发送错误后关闭，所以这里会抛出WebSocketDisconnect


if __name__ == "__main__":
    pytest.main([__file__])
