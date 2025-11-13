"""量化交易系统常量定义"""

# Define constants used across the application

# 交易相关常量
MIN_TRADE_QUANTITY = 100  # 最小交易单位（股）
TRADE_QUANTITY_MULTIPLE = 100  # 交易数量必须是100的整数倍

# 策略参数默认值
DEFAULT_INITIAL_CASH = 1000000.0  # 默认初始资金（100万）
DEFAULT_COMMISSION_RATE = 0.0003  # 默认佣金率（万分之三）
MIN_COMMISSION = 5.0  # 最低佣金（元）
STAMP_TAX_RATE = 0.001  # 印花税税率（千分之一）

# 回测相关
DEFAULT_BACKTEST_START_DATE = "2023-01-01"  # 默认回测开始日期
DEFAULT_BACKTEST_END_DATE = "2023-12-31"  # 默认回测结束日期
DEFAULT_REBALANCE_INTERVAL = 5  # 默认调仓周期（交易日）
MAX_DD_THRESHOLD = 0.5  # 最大回撤阈值（50%）
MAX_POSITION_SIZE = 0.3  # 单个股票最大仓位比例
MAX_CASH_RATIO = 0.2  # 最大现金比例
SLIPPAGE_RATE = 0.001  # 滑点率（0.1%）
COMMISSION_RATE = 0.0002  # 佣金率（0.02%）

# 策略相关常量
STRATEGY_TIMEOUT = 60 * 60  # 策略执行超时时间（秒）
MAX_STRATEGY_PARAMS = 20  # 最大策略参数数量

# 数据相关常量
DEFAULT_START_DATE = "2020-01-01"
DEFAULT_END_DATE = "2023-12-31"
MAX_BATCH_SIZE = 100  # 批量数据加载的最大数量
CACHE_EXPIRY = 3600  # 缓存过期时间（秒）

# 订单相关常量
ORDER_TYPES = ['market', 'limit', 'stop', 'stop_limit']
ORDER_SIDES = ['buy', 'sell']
ORDER_STATUS = ['pending', 'filled', 'partially_filled', 'cancelled', 'rejected']
ORDER_STATUS_PENDING = "pending"
ORDER_STATUS_FILLED = "filled"
ORDER_STATUS_CANCELLED = "cancelled"
ORDER_STATUS_REJECTED = "rejected"

# 交易方向常量
ORDER_SIDE_BUY = "buy"
ORDER_SIDE_SELL = "sell"

# 性能指标相关常量
RISK_FREE_RATE = 0.03  # 无风险利率
TRADING_DAYS_PER_YEAR = 252  # 每年交易日数量

# 滑点范围配置
SLIP_RANGE = [-0.0005, 0.0005]  # 滑点范围（-0.05% 到 0.05%）

# 技术指标默认参数
DEFAULT_MA_SHORT_WINDOW = 20  # 默认短期均线窗口
DEFAULT_MA_LONG_WINDOW = 50  # 默认长期均线窗口
DEFAULT_RSI_WINDOW = 14  # 默认RSI计算窗口
DEFAULT_RSI_OVERSOLD = 30  # 默认RSI超卖阈值
DEFAULT_RSI_OVERBOUGHT = 70  # 默认RSI超买阈值
DEFAULT_MOMENTUM_WINDOW = 20  # 默认动量计算窗口

# 信号类型常量
SIGNAL_TYPE_GOLDEN_CROSS = "golden_cross"  # 金叉
SIGNAL_TYPE_DEATH_CROSS = "death_cross"  # 死叉
SIGNAL_TYPE_OVERSOLD = "oversold"  # 超卖
SIGNAL_TYPE_OVERBOUGHT = "overbought"  # 超买
SIGNAL_TYPE_MOMENTUM = "momentum"  # 动量
SIGNAL_TYPE_ENTER = "enter"  # 入场
SIGNAL_TYPE_EXIT = "exit"  # 出场

# 默认股票池（示例）
DEFAULT_STOCK_POOL = [
    "000001.SZ",  # 平安银行
    "000002.SZ",  # 万科A
    "000858.SZ",  # 五粮液
    "002415.SZ",  # 海康威视
    "600036.SH",  # 招商银行
    "600519.SH",  # 贵州茅台
    "600900.SH",  # 长江电力
    "601318.SH",  # 中国平安
    "601398.SH",  # 工商银行
    "601857.SH"   # 中国石油
]

# 数据库相关
DB_CONNECTION_URL = "sqlite:///data/quant.db"  # 数据库连接URL

# API相关
API_PREFIX = "/api/v1"  # API前缀
API_VERSION = "v1"  # API版本

# 响应状态码
SUCCESS_CODE = 200  # 成功
ERROR_CODE = 500  # 内部错误
BAD_REQUEST_CODE = 400  # 请求错误
NOT_FOUND_CODE = 404  # 资源不存在

# 日志相关
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
LOG_LEVEL = "INFO"  # 默认日志级别

# 数据字段映射
DATA_FIELD_MAPPING = {
    'open': '开盘价',
    'high': '最高价',
    'low': '最低价',
    'close': '收盘价',
    'volume': '成交量',
    'amount': '成交额'
}

# 性能指标名称映射
METRIC_NAME_MAPPING = {
    'total_return': '总收益率',
    'annual_return': '年化收益率',
    'annual_volatility': '年化波动率',
    'max_drawdown': '最大回撤',
    'sharpe_ratio': '夏普比率',
    'sortino_ratio': '索提诺比率',
    'win_rate': '胜率',
    'profit_factor': '盈利因子',
    'trades_count': '交易次数'
}

# 原有系统常量
AK_SLEEP = 0.5
MAX_RETRY = 3
WORKER_MAX_MEM = 2_000_000_000
BATCH_SIZE = 1000
QUALITY_SCORE_MIN = 60
FACTOR_WEIGHTS = {"return": 0.4, "stability": 0.3, "active": 0.2, "quality": 0.1}

# Other defaults
DEFAULT_PYTHON = "3.11.7"
DEFAULT_NODE = "18.19.0"
