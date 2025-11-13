"""回测示例脚本"""

from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from quant_web.core.be.trading_engine import TradingEngine
from quant_web.core.be.data_feed import DataFeed
from quant_web.core.const import DEFAULT_STOCK_POOL, DEFAULT_INITIAL_CASH


def main():
    """运行回测示例"""
    # 将输出写入文件以便调试
    log_file = "backtest_log.txt"
    with open(log_file, "w") as f:
        f.write(f"=== 回测示例开始 ===\n")
        f.write(f"当前时间: {datetime.now()}\n")
        
        # 创建交易引擎
        f.write("创建交易引擎...\n")
        engine = TradingEngine()
        f.write(f"初始化交易引擎，初始资金: {DEFAULT_INITIAL_CASH}\n")
        engine.initialize(initial_cash=DEFAULT_INITIAL_CASH)
        
        # 创建数据馈送并加载数据
        f.write("创建数据馈送...\n")
        data_feed = DataFeed()
        
        # 设置回测时间范围（最近一年）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        f.write(f"设置回测时间范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}\n")
        # 使用默认股票池的前5只股票进行测试
        f.write(f"默认股票池: {DEFAULT_STOCK_POOL}\n")
        stock_pool = DEFAULT_STOCK_POOL[:5]
        f.write(f"使用的股票池: {stock_pool}\n")
        f.write("开始加载历史数据...\n")
        success = data_feed.load_historical_data(stock_pool, start_date, end_date)
        f.write(f"数据加载结果: {'成功' if success else '失败'}\n")
        f.write(f"加载的股票数量: {len(data_feed.get_available_stocks())}\n")
        trading_dates = data_feed.get_trading_dates(start_date, end_date)
        f.write(f"交易日期数量: {len(trading_dates)}\n")
        
        # 添加一个简单的测试
        if trading_dates:
            first_date = trading_dates[0]
            f.write(f"第一个交易日期: {first_date}\n")
            test_data = data_feed.get_data_for_date(first_date)
            f.write(f"第一个日期的数据数量: {len(test_data)}\n")
            # 显示一些数据样例
            if test_data:
                for ts_code, data in test_data.items():
                    f.write(f"  股票 {ts_code} 的数据键: {list(data.keys())}\n")
                    break  # 只显示第一个股票的数据结构
        
        f.write("将数据馈送加载到交易引擎...\n")
        engine.load_data_feed(data_feed)
        
        # 显示可用策略
        f.write("\n可用策略列表:\n")
        available_strategies = engine._get_available_strategies()
        f.write(f"可用策略: {available_strategies}\n")
        
        # 添加策略1：移动平均线策略
        f.write("\n添加移动平均线策略\n")
        try:
            ma_strategy = engine.add_strategy(
                strategy_name="moving_average",
                strategy_id="ma_strategy_001",
                parameters={
                    'short_window': 20,
                    'long_window': 60,
                    'position_ratio': 0.1
                }
            )
            f.write("移动平均线策略添加成功\n")
            # 检查策略属性
            f.write(f"策略类型: {type(ma_strategy)}\n")
            f.write(f"策略属性: {dir(ma_strategy)}\n")
        except Exception as e:
            f.write(f"移动平均线策略添加失败: {str(e)}\n")
        
        # 直接运行交易引擎的回测方法
        f.write("\n使用交易引擎内置的回测方法...\n")
        try:
            # 只使用最近的30个交易日进行测试
            test_start = end_date - timedelta(days=60)  # 使用更长的时间来确保有足够的数据计算指标
            f.write(f"使用简化时间范围: {test_start.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}\n")
            
            # 运行内置回测
            result = engine.execute_backtest(test_start, end_date)
            
            # 分析回测结果
            f.write("\n回测结果分析:\n")
            f.write(f"结果类型: {type(result)}\n")
            f.write(f"结果键: {list(result.keys())}\n")
            
            # 检查订单历史
            if 'order_history' in result:
                f.write(f"\n订单历史数量: {len(result['order_history'])}\n")
                # 显示前几个订单
                for i, order in enumerate(result['order_history'][:3]):
                    f.write(f"  订单 {i+1}: {order}\n")
            
            # 检查每日净值
            if 'daily_equity' in result:
                f.write(f"\n每日净值记录数量: {len(result['daily_equity'])}\n")
                # 显示第一个和最后一个记录
                if result['daily_equity']:
                    first_eq = result['daily_equity'][0]
                    last_eq = result['daily_equity'][-1]
                    f.write(f"  第一个记录: {first_eq}\n")
                    f.write(f"  最后一个记录: {last_eq}\n")
                    # 计算收益率
                    first_value = first_eq['equity']
                    last_value = last_eq['equity']
                    f.write(f"  收益率: {(last_value / first_value - 1) * 100:.2f}%\n")
            
            # 检查绩效指标
            if 'performance_metrics' in result:
                f.write("\n绩效指标:\n")
                for key, value in result['performance_metrics'].items():
                    f.write(f"  {key}: {value}\n")
                    
        except Exception as e:
            import traceback
            f.write(f"回测执行失败: {str(e)}\n")
            f.write(f"错误栈: {traceback.format_exc()}\n")
        
        f.write("\n=== 回测示例完成 ===\n")
    
    print(f"回测日志已写入 {log_file}")
    # 读取并显示日志文件内容
    try:
        with open(log_file, "r") as f:
            content = f.read()
            print("\n日志内容:")
            print(content)
    except Exception as e:
        print(f"无法读取日志文件: {str(e)}")


if __name__ == "__main__":
    main()
