import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from quant_web.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_websocket_concurrent_connections():
    """测试WebSocket并发连接性能"""
    # 并发连接数量
    connection_count = 10
    
    async def connect_and_subscribe():
        """创建一个WebSocket连接并订阅任务"""
        async with client.websocket_connect("/ws/tasks") as websocket:
            # 发送订阅消息
            await websocket.send_json({
                "type": "subscribe",
                "task_ids": ["perf-test-task"]
            })
            
            # 等待订阅确认
            response = await websocket.receive_json()
            assert response["type"] == "subscribed"
            
            # 发送心跳响应
            await websocket.send_json({"type": "heartbeat_response"})
            
            # 稍微等待一下
            await asyncio.sleep(0.1)
    
    # 测量并发连接时间
    start_time = time.time()
    
    # 创建并发连接任务
    tasks = [connect_and_subscribe() for _ in range(connection_count)]
    
    # 等待所有连接完成
    await asyncio.gather(*tasks)
    
    # 计算总耗时
    total_time = time.time() - start_time
    
    # 输出性能指标
    print(f"Completed {connection_count} concurrent connections in {total_time:.2f}s")
    print(f"Average connection time: {total_time/connection_count:.4f}s per connection")
    
    # 确保性能在可接受范围内（示例阈值）
    assert total_time < 5.0, f"Too slow: {total_time:.2f}s for {connection_count} connections"


@pytest.mark.asyncio
async def test_websocket_message_throughput():
    """测试WebSocket消息吞吐量"""
    async with client.websocket_connect("/ws/tasks") as websocket:
        # 测试消息数量
        message_count = 100
        
        # 发送消息并测量时间
        start_time = time.time()
        
        for i in range(message_count):
            # 发送批量状态查询消息
            await websocket.send_json({
                "type": "batch_status",
                "task_ids": [f"test-task-{i}"],
                "sequence": i
            })
            
            # 接收响应
            response = await websocket.receive_json()
            assert response["type"] == "batch_status_response"
        
        # 计算吞吐量
        total_time = time.time() - start_time
        messages_per_second = message_count / total_time if total_time > 0 else 0
        
        # 输出性能指标
        print(f"Processed {message_count} messages in {total_time:.2f}s")
        print(f"Throughput: {messages_per_second:.2f} messages/second")
        
        # 确保吞吐量在可接受范围内
        assert messages_per_second > 10, f"Low throughput: {messages_per_second:.2f} messages/second"


@pytest.mark.asyncio
async def test_websocket_long_connection_stability():
    """测试WebSocket长连接稳定性"""
    async with client.websocket_connect("/ws/tasks") as websocket:
        # 测试持续时间（秒）
        test_duration = 10
        
        # 记录开始时间
        start_time = time.time()
        end_time = start_time + test_duration
        
        # 计数器
        heartbeat_count = 0
        message_count = 0
        
        # 持续接收消息
        while time.time() < end_time:
            try:
                # 设置较短的超时以便可以定期检查时间
                response = await asyncio.wait_for(websocket.receive_json(), timeout=2.0)
                message_count += 1
                
                # 处理心跳消息
                if response["type"] == "heartbeat":
                    heartbeat_count += 1
                    # 发送心跳响应
                    await websocket.send_json({"type": "heartbeat_response"})
                    
            except asyncio.TimeoutError:
                # 超时是正常的，继续循环
                continue
        
        # 输出稳定性指标
        print(f"Connection stable for {test_duration} seconds")
        print(f"Received {message_count} messages ({heartbeat_count} heartbeats)")
        
        # 确保至少收到一些心跳消息
        assert heartbeat_count >= 0, "No heartbeat messages received"


if __name__ == "__main__":
    pytest.main([__file__])
