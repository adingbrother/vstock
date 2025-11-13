import asyncio
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from quant_web.core.tasks import BacktestTask, start_backtest_task
from quant_web.core.task_manager import global_task_manager


async def test_backtest_task():
    """测试回测任务执行流程"""
    print("开始测试回测任务...")
    
    # 生成任务ID
    task_id = f"TEST_{int(time.time() * 1000)}"
    print(f"创建任务ID: {task_id}")
    
    # 准备回测参数
    strategy_config = {
        "name": "moving_average",
        "parameters": {
            "short_window": 20,
            "long_window": 60,
            "position_ratio": 0.1
        }
    }
    
    # 使用少量股票进行测试
    stock_pool = ['000001.SZ', '000002.SZ']
    
    # 使用较短的时间范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)  # 使用60天数据
    
    print(f"回测时间范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
    print(f"使用股票: {stock_pool}")
    print(f"策略配置: {strategy_config}")
    
    # 创建消息队列
    queue = asyncio.Queue()
    
    # 定义一个协程来监听队列消息
    async def listen_for_messages():
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=5.0)
                print(f"收到消息: {message}")
                
                # 如果收到完成或错误消息，则退出循环
                if message.get('type') in ['done', 'error']:
                    break
            except asyncio.TimeoutError:
                # 超时，检查任务状态
                task = global_task_manager.get_task(task_id)
                if task:
                    print(f"当前任务状态: {task.status.value}, 进度: {task.progress:.1%}")
                else:
                    print("任务不存在于全局任务管理器中")
    
    # 启动消息监听任务
    listener_task = asyncio.create_task(listen_for_messages())
    
    try:
        # 执行回测任务
        print("开始执行回测任务...")
        await start_backtest_task(
            task_id=task_id,
            strategy_config=strategy_config,
            stock_pool=stock_pool,
            start_date=start_date,
            end_date=end_date,
            queue=queue
        )
        
        # 等待消息监听任务完成
        await listener_task
        
        # 获取任务结果
        task = global_task_manager.get_task(task_id)
        if task:
            print(f"\n任务执行完成")
            print(f"任务状态: {task.status.value}")
            print(f"任务进度: {task.progress:.1%}")
            
            if task.result:
                print(f"\n回测结果:")
                print(f"- 股票数量: {task.result.get('stock_count')}")
                print(f"- 策略名称: {task.result.get('strategy_config', {}).get('name')}")
                
                backtest_result = task.result.get('backtest_result', {})
                if backtest_result:
                    # 打印订单历史
                    order_history = backtest_result.get('order_history', [])
                    print(f"\n订单历史 (共{len(order_history)}个订单):")
                    for i, order in enumerate(order_history[:3], 1):
                        print(f"  {i}. {order}")
                    
                    # 打印绩效指标
                    metrics = backtest_result.get('performance_metrics', {})
                    if metrics:
                        print(f"\n绩效指标:")
                        print(f"  - 总收益率: {metrics.get('total_return', 0) * 100:.2f}%")
                        print(f"  - 年化收益率: {metrics.get('annual_return', 0) * 100:.2f}%")
                        print(f"  - 夏普比率: {metrics.get('sharpe_ratio', 0):.2f}")
            else:
                print(f"任务没有返回结果")
                if task.error:
                    print(f"错误信息: {task.error}")
        else:
            print("无法在全局任务管理器中找到任务")
            
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 取消消息监听任务
        if not listener_task.done():
            listener_task.cancel()
        
        print("\n测试结束")


if __name__ == "__main__":
    # 运行异步测试
    asyncio.run(test_backtest_task())
