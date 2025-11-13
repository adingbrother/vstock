import asyncio
import websockets
import json
import time

async def test_websocket_heartbeat():
    """测试WebSocket连接和心跳响应"""
    try:
        # 连接到WebSocket端点
        async with websockets.connect("ws://127.0.0.1:8000/ws/tasks") as websocket:
            print("成功连接到WebSocket服务")
            
            # 记录开始时间
            start_time = time.time()
            
            # 等待接收心跳消息
            print("等待接收心跳消息...")
            
            # 设置超时时间为35秒（心跳间隔为30秒）
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=35)
                print(f"接收到消息: {message}")
                
                # 解析消息
                data = json.loads(message)
                
                # 检查是否为心跳消息
                if data.get("type") == "heartbeat":
                    print("✓ 成功接收到心跳消息")
                    
                    # 发送心跳响应
                    heartbeat_response = {
                        "type": "heartbeat_response",
                        "timestamp": time.time()
                    }
                    await websocket.send(json.dumps(heartbeat_response))
                    print("✓ 已发送心跳响应")
                    
                    # 等待一会儿再关闭连接
                    await asyncio.sleep(2)
                    print("测试成功完成！")
                    return True
                else:
                    print(f"接收到非心跳消息: {data.get('type')}")
                    return False
                    
            except asyncio.TimeoutError:
                print("✗ 超时：未在35秒内收到心跳消息")
                return False
                
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"✗ 连接关闭错误: {e}")
        return False
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"✗ 无效的状态码: {e}")
        return False
    except Exception as e:
        print(f"✗ 发生错误: {e}")
        return False

# 运行测试
if __name__ == "__main__":
    print("开始测试WebSocket连接和心跳...")
    result = asyncio.run(test_websocket_heartbeat())
    if result:
        print("\n测试通过！WebSocket连接正常工作")
    else:
        print("\n测试失败！WebSocket连接存在问题")
