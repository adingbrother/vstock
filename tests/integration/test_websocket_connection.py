import asyncio
import json
import socket
import traceback
from websockets.asyncio.client import connect

async def test_websocket_connection():
    """
    简化版WebSocket连接测试，只测试基本连接功能
    """
    print("===== WebSocket连接测试开始 =====")
    
    # 先检查端口是否开放
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex(("localhost", 8000))
        sock.close()
        if result == 0:
            print("✓ 端口8000已开放，服务器正在监听")
        else:
            print("✗ 端口8000未开放，请确保后端服务正在运行")
            return
    except Exception as e:
        print(f"✗ 端口检查失败: {e}")
        return
    
    websocket = None
    
    try:
        print("正在尝试建立WebSocket连接...")
        
        # 最简化的连接测试
        websocket = await connect("ws://localhost:8000/ws/tasks")
        
        print("✓ WebSocket连接成功建立！")
        
        # 发送简单的心跳消息
        print("发送测试消息...")
        await websocket.send_json({"type": "heartbeat_response"})
        print("✓ 测试消息发送成功")
        
        # 等待一小段时间，看是否有响应
        try:
            print("等待服务器响应...")
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"✓ 收到服务器响应: {response[:100]}...")
        except asyncio.TimeoutError:
            print("⚠ 未收到服务器响应，但连接可能仍然有效")
        
    except Exception as e:
        print(f"✗ WebSocket连接失败: {str(e)}")
        print("\n详细错误信息:")
        traceback.print_exc()
        
    finally:
        print("\n===== WebSocket测试结束 =====")
        
        # 确保关闭连接
        if websocket:
            try:
                await websocket.close()
                print("✓ WebSocket连接已关闭")
            except Exception as e:
                print(f"✗ 关闭WebSocket连接时出错: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_websocket_connection())
