import asyncio
import threading

# 添加线程锁以保护共享状态，防止并发访问问题
_QUEUE_LOCK = threading.RLock()

# 队列最大大小，防止内存泄漏
MAX_QUEUE_SIZE = 100

# 任务队列映射 (task_id -> asyncio.Queue)
TASK_QUEUES: dict[str, asyncio.Queue] = {}

# 连接映射 (connection_id -> set(task_ids))
CONNECTION_SUBSCRIPTIONS: dict[str, set] = {}

# 连接订阅锁
_CONNECTION_LOCK = threading.RLock()

# 过期任务清理时间（秒）
TASK_EXPIRY_TIME = 3600  # 1小时

# 任务最后活动时间映射
task_last_activity: dict[str, float] = {}

# 活动时间锁
_ACTIVITY_LOCK = threading.RLock()


def get_task_queue(task_id: str) -> asyncio.Queue:
    """线程安全地获取或创建任务队列"""
    with _QUEUE_LOCK:
        if task_id not in TASK_QUEUES:
            # 创建有界队列，限制最大大小
            TASK_QUEUES[task_id] = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
        return TASK_QUEUES[task_id]


def remove_task_queue(task_id: str) -> bool:
    """线程安全地移除任务队列"""
    with _QUEUE_LOCK:
        if task_id in TASK_QUEUES:
            del TASK_QUEUES[task_id]
            return True
        return False


def update_task_activity(task_id: str):
    """更新任务的最后活动时间"""
    with _ACTIVITY_LOCK:
        task_last_activity[task_id] = asyncio.get_event_loop().time()


def add_connection_subscription(connection_id: str, task_ids: list):
    """添加连接订阅"""
    with _CONNECTION_LOCK:
        if connection_id not in CONNECTION_SUBSCRIPTIONS:
            CONNECTION_SUBSCRIPTIONS[connection_id] = set()
        CONNECTION_SUBSCRIPTIONS[connection_id].update(task_ids)


def remove_connection_subscription(connection_id: str, task_ids: list):
    """移除连接订阅"""
    with _CONNECTION_LOCK:
        if connection_id in CONNECTION_SUBSCRIPTIONS:
            for task_id in task_ids:
                CONNECTION_SUBSCRIPTIONS[connection_id].discard(task_id)


def remove_connection(connection_id: str):
    """移除整个连接"""
    with _CONNECTION_LOCK:
        if connection_id in CONNECTION_SUBSCRIPTIONS:
            del CONNECTION_SUBSCRIPTIONS[connection_id]
