-- init.sql: complete schema for QuantWeb platform
-- 股票基本信息表
CREATE TABLE IF NOT EXISTS stock_basic (
    ts_code TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    name TEXT NOT NULL,
    area TEXT,
    industry TEXT,
    list_date TEXT,
    data_source TEXT DEFAULT 'akshare' CHECK(data_source IN ('akshare','tushare')),
    status INTEGER DEFAULT 1 CHECK(status IN (0,1)),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sb_industry ON stock_basic(industry);

-- 策略表
CREATE TABLE IF NOT EXISTS strategy (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    params_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- 通用任务表
CREATE TABLE IF NOT EXISTS task (
    id TEXT PRIMARY KEY,
    task_type TEXT NOT NULL,
    priority TEXT DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'pending',
    progress REAL DEFAULT 0.0,
    parameters TEXT,
    result TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_task_type ON task(task_type);
CREATE INDEX IF NOT EXISTS idx_task_status ON task(status);

-- 回测任务表
CREATE TABLE IF NOT EXISTS backtest_task (
    id TEXT PRIMARY KEY,
    strategy_id TEXT,
    stock_pool TEXT,
    start_date TEXT,
    end_date TEXT,
    init_cash REAL,
    status TEXT CHECK(status IN ('Pending','Running','Success','Failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_path TEXT
);

-- 推荐结果表
CREATE TABLE IF NOT EXISTS recommend_result (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    trade_date TEXT,
    rank INTEGER,
    ts_code TEXT,
    score REAL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_rec_task ON recommend_result(task_id);

-- 数据下载日志表
CREATE TABLE IF NOT EXISTS data_download_log (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    ts_code TEXT,
    status TEXT,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_dl_task ON data_download_log(task_id);

-- K线数据表模板注释
-- 实际使用时会根据股票代码动态创建，如 kline_000001_sz
-- CREATE TABLE IF NOT EXISTS kline_{ts_code_lower} (
--     trade_date DATE NOT NULL,
--     open REAL NOT NULL CHECK(open >= 0),
--     high REAL NOT NULL CHECK(high >= 0),
--     low REAL NOT NULL CHECK(low >= 0),
--     close REAL NOT NULL CHECK(close >= 0),
--     vol INTEGER NOT NULL CHECK(vol >= 0),
--     amount REAL NOT NULL CHECK(amount >= 0),
--     source TEXT CHECK(source IN ('akshare','tushare')),
--     PRIMARY KEY (trade_date)
-- );
