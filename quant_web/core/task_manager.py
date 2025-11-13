from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, List, Tuple, Type
from dataclasses import dataclass
import uuid
import threading
from queue import PriorityQueue, Empty
from collections import deque
import time
import json
from datetime import datetime
import logging

from quant_web.core.exceptions import TaskError
from sqlalchemy.orm import Session

# 导入数据库会话和模型
from models.database import SessionLocal
from quant_web.models.models import Task as TaskModel

# 配置日志
logger = logging.getLogger(__name__)

# 从环境变量读取日志级别，默认为INFO
import os
log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
# 将字符串日志级别转换为logging模块的级别常量
level_mapping = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'WARN': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
logger.setLevel(level_mapping.get(log_level, logging.INFO))

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(level_mapping.get(log_level, logging.INFO))

# 创建文件处理器
# 确保logs目录存在
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'task_manager.log')
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(level_mapping.get(log_level, logging.INFO))

# 设置日志格式，添加线程ID等上下文信息
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - [Thread:%(threadName)s] - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# 添加处理器到logger
if not logger.handlers:
    logger.addHandler(console_handler)
logger.addHandler(file_handler)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class TaskResult:
    """任务结果数据类"""
    success: bool
    data: Any = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式以便存储"""
        return {
            "success": self.success,
            "data": self.data,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskResult':
        """从字典创建TaskResult对象"""
        return cls(
            success=data["success"],
            data=data.get("data"),
            error_message=data.get("error_message")
        )


import json
from datetime import datetime

class BaseTask(ABC):
    """任务抽象基类"""
    
    def __init__(self, task_id: Optional[str] = None, priority: TaskPriority = TaskPriority.MEDIUM):
        self.task_id = task_id or str(uuid.uuid4())
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.progress = 0.0
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        self.result = None
        self.error_message = None
        self.task_type = self.__class__.__name__  # 任务类型，用于持久化
        self.parameters = {}  # 任务参数，用于持久化
    
    @abstractmethod
    def execute(self) -> TaskResult:
        """执行任务的抽象方法"""
        pass
    
    def update_progress(self, progress: float) -> None:
        """更新任务进度"""
        self.progress = min(max(0.0, progress), 1.0)
    
    def start(self) -> None:
        """开始任务"""
        from datetime import datetime
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete(self, result: TaskResult) -> None:
        """完成任务"""
        from datetime import datetime
        self.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        self.result = result.data
        self.error_message = result.error_message
        self.completed_at = datetime.utcnow()
    
    def cancel(self) -> None:
        """取消任务"""
        if self.status == TaskStatus.PENDING or self.status == TaskStatus.RUNNING:
            self.status = TaskStatus.CANCELLED
    
    def to_dict(self) -> Dict[str, Any]:
        """将任务转换为字典格式，用于持久化"""
        return {
            "task_id": self.task_id,
            "priority": self.priority.value,
            "status": self.status.value,
            "progress": self.progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": json.dumps(self.result) if self.result is not None else None,
            "error_message": self.error_message,
            "parameters": json.dumps(self.parameters) if self.parameters else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseTask':
        """从字典创建任务对象"""
        task = cls(
            task_id=data.get('task_id'),
            priority=TaskPriority(data.get('priority', TaskPriority.MEDIUM.value))
        )
        task.status = TaskStatus(data.get('status', TaskStatus.PENDING.value))
        task.progress = data.get('progress', 0.0)
        
        # 处理时间字段
        from datetime import datetime
        if isinstance(data.get('created_at'), str):
            task.created_at = datetime.fromisoformat(data['created_at'])
        else:
            task.created_at = data.get('created_at')
            
        if isinstance(data.get('started_at'), str):
            task.started_at = datetime.fromisoformat(data['started_at'])
        else:
            task.started_at = data.get('started_at')
            
        if isinstance(data.get('completed_at'), str):
            task.completed_at = datetime.fromisoformat(data['completed_at'])
        else:
            task.completed_at = data.get('completed_at')
            
        task.error_message = data.get('error_message')
        task.result = json.loads(data.get('result')) if data.get('result') else None
        task.parameters = json.loads(data.get('parameters')) if data.get('parameters') else {}
        return task


class TaskFactory:
    """任务工厂类"""
    
    _task_registry: Dict[str, type] = {}
    
    @classmethod
    def register_task(cls, task_type: str, task_class: type) -> None:
        """注册任务类型"""
        if not issubclass(task_class, BaseTask):
            raise TaskError(
                message=f"Task class must inherit from BaseTask",
                error_code="INVALID_TASK_CLASS",
                details={"task_class": str(task_class)}
            )
        cls._task_registry[task_type] = task_class
        # 同时注册类名，方便从数据库加载时查找
        cls._task_registry[task_class.__name__] = task_class
    
    @classmethod
    def create_task(cls, task_type: str, **kwargs) -> BaseTask:
        """创建任务实例"""
        if task_type not in cls._task_registry:
            print(f"Unknown task type: {task_type}, creating default BaseTask")
            # 如果找不到任务类型，返回一个通用的任务实例
            # 由于BaseTask是抽象类，我们需要一个具体的实现
            class GenericTask(BaseTask):
                def execute(self) -> TaskResult:
                    return TaskResult(success=False, error_message="Generic task cannot be executed")
            return GenericTask(**kwargs)
        
        task_class = cls._task_registry[task_type]
        return task_class(**kwargs)
    
    @classmethod
    def get_available_tasks(cls) -> list[str]:
        """获取所有可用的任务类型"""
        return list(cls._task_registry.keys())


class TaskManager:
    """任务管理器"""
    
    def __init__(self, max_workers: int = 4, default_timeout: int = 3600):
        """初始化任务管理器"""
        # 最大工作线程数
        self.max_workers = max_workers
        # 默认任务超时时间（秒）
        self.default_timeout = default_timeout
        # 内存中的任务存储
        self.tasks: Dict[str, BaseTask] = {}
        # 优先级队列
        self.task_queue = PriorityQueue()
        # 工作线程池
        self.workers: List[threading.Thread] = []
        # 线程锁
        self.lock = threading.RLock()
        # 停止标志
        self.stop_event = threading.Event()
        # 数据库会话
        self.db_session = None
        # 任务重试配置
        self.max_retries = 3
        # 重试间隔（秒）
        self.retry_delay = 10
        
        # 初始化数据库会话
        self._init_db_session()
        
        # 初始化工作线程
        self._init_workers()
        # 从数据库加载任务
        self._load_pending_tasks()
        
        logger.info(f"TaskManager initialized with max_workers={max_workers}, default_timeout={default_timeout}")
        
    def _load_pending_tasks(self) -> None:
        """从数据库加载待处理和运行中的任务"""
        try:
            # 确保数据库会话有效
            if not self.db_session or not self.db_session.is_active:
                self._init_db_session()
            
            if not self.db_session:
                logger.error("Cannot load tasks: No active database session")
                return
            
            # 加载待处理的任务
            pending_tasks = self._load_tasks_from_db_by_status(TaskStatus.PENDING)
            # 加载可能在系统重启前运行中的任务
            running_tasks = self._load_tasks_from_db_by_status(TaskStatus.RUNNING)
            
            # 将运行中的任务重新标记为待处理并优先处理
            for task in running_tasks:
                task.status = TaskStatus.PENDING
                self._save_task_to_db(task)
                # 添加到优先级队列
                if hasattr(task, 'priority') and task.priority:
                    self.task_queue.put((task.priority.value, task.task_id))
                else:
                    self.task_queue.put((TaskPriority.MEDIUM.value, task.task_id))
                logger.info(f"Reloaded running task as pending: {task.task_id}")
            
            # 添加待处理任务到队列
            for task in pending_tasks:
                if hasattr(task, 'priority') and task.priority:
                    self.task_queue.put((task.priority.value, task.task_id))
                else:
                    self.task_queue.put((TaskPriority.MEDIUM.value, task.task_id))
                logger.info(f"Loaded pending task: {task.task_id}")
            
            logger.info(f"Total loaded tasks: {len(running_tasks) + len(pending_tasks)}")
        except Exception as e:
            logger.error(f"Failed to load pending tasks: {str(e)}")
            # 尝试重新创建数据库会话
            try:
                self._init_db_session()
                logger.info("Database session recreated")
            except Exception as db_error:
                logger.error(f"Failed to recreate database session: {str(db_error)}")
    
    def get_task_progress(self, task_id: str) -> Dict[str, Any]:
        """获取任务进度和详细信息"""
        task = self._get_task(task_id)
        if not task:
            return {
                "task_id": task_id,
                "status": "NOT_FOUND",
                "progress": 0
            }
        
        # 构建详细的任务进度信息
        progress_info = {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "status": task.status.name,
            "progress": task.progress,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": getattr(task, 'result', None),
            "error_message": getattr(task, 'error_message', None)
        }
        
        # 添加优先级信息
        if hasattr(task, 'priority') and task.priority:
            progress_info["priority"] = task.priority.name
        
        # 添加失败计数
        if hasattr(task, 'fail_count'):
            progress_info["fail_count"] = task.fail_count
        
        # 添加参数信息
        if hasattr(task, 'parameters'):
            progress_info["parameters"] = task.parameters
        
        return progress_info
    
    def add_task(self, task: BaseTask) -> str:
        """添加任务到队列，确保线程安全"""
        try:
            with self.lock:
                # 验证任务类型
                if not isinstance(task, BaseTask):
                    raise ValueError("Task must be an instance of BaseTask")
                
                # 生成任务ID
                if not task.task_id:
                    task.task_id = str(uuid.uuid4())
                
                # 设置任务默认属性
                if not task.status:
                    task.status = TaskStatus.PENDING
                if not hasattr(task, 'priority') or not task.priority:
                    task.priority = TaskPriority.MEDIUM
                if not hasattr(task, 'parameters'):
                    task.parameters = {}
                if not hasattr(task, 'progress'):
                    task.progress = 0
                if not task.created_at:
                    from datetime import datetime
                    task.created_at = datetime.now()
                
                # 保存任务到内存
                self.tasks[task.task_id] = task
                logger.debug(f"Task {task.task_id} added to memory")
            
            # 保存任务到数据库
            self._save_task_to_db(task)
            
            # 将任务添加到队列
            with self.lock:
                self.task_queue.put((task.priority.value, task.task_id))
            
            logger.info(f"Task {task.task_id} added to queue with priority {task.priority.name}")
            return task.task_id
        except Exception as e:
            logger.error(f"Error adding task {task.task_id}: {str(e)}")
            raise TaskError(
                message="Failed to add task",
                error_code="TASK_ADD_ERROR",
                details={"task_id": task.task_id, "error": str(e)}
            )
    
    def get_task(self, task_id: str) -> Optional[BaseTask]:
        """获取任务"""
        if task_id in self.tasks:
            return self.tasks[task_id]
        # 从数据库加载
        return self._load_task_from_db(task_id)
    
    def get_tasks_by_status(self, status: TaskStatus) -> list[BaseTask]:
        """根据状态获取任务"""
        # 先从内存中查找
        memory_tasks = [task for task in self.tasks.values() if task.status == status]
        
        # 再从数据库中查找
        db_tasks = self._load_tasks_from_db_by_status(status)
        
        # 合并结果，避免重复
        task_ids = {task.task_id for task in memory_tasks}
        for task in db_tasks:
            if task.task_id not in task_ids:
                memory_tasks.append(task)
                self.tasks[task.task_id] = task
                task_ids.add(task.task_id)
        
        return memory_tasks
    
    def remove_task(self, task_id: str) -> None:
        """移除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
        self._delete_task_from_db(task_id)
    
    def get_all_tasks(self) -> list[BaseTask]:
        """获取所有任务"""
        # 加载所有数据库中的任务到内存
        db_tasks = self._load_all_tasks_from_db()
        for task in db_tasks:
            if task.task_id not in self.tasks:
                self.tasks[task.task_id] = task
        
        return list(self.tasks.values())
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> None:
        """更新任务状态"""
        task = self.get_task(task_id)
        if task:
            task.status = status
            self._update_task_in_db(task)
    
    def _save_task_to_db(self, task: BaseTask) -> None:
        """保存任务到数据库，增强错误处理和事务管理"""
        # 确保数据库会话有效
        if not self.db_session or not self.db_session.is_active:
            self._init_db_session()
            if not self.db_session:
                logger.error(f"Failed to initialize database session for task {task.task_id}")
                return
        
        try:
            # 查询是否已存在相同ID的任务
            existing_task = self.db_session.query(TaskModel).filter(TaskModel.id == task.task_id).first()
            
            if existing_task:
                # 更新现有任务
                existing_task.task_type = task.task_type
                existing_task.priority = task.priority.value
                existing_task.status = task.status.value
                existing_task.progress = task.progress
                existing_task.created_at = task.created_at
                existing_task.started_at = task.started_at
                existing_task.completed_at = task.completed_at
                
                # 安全处理JSON序列化
                try:
                    existing_task.result = json.dumps(task.result) if task.result is not None else None
                except (TypeError, ValueError) as json_error:
                    existing_task.result = json.dumps({"error": "Failed to serialize result"})
                    logger.warning(f"Failed to serialize result for task {task.task_id}: {str(json_error)}")
                
                try:
                    existing_task.parameters = json.dumps(task.parameters) if task.parameters else None
                except (TypeError, ValueError) as json_error:
                    existing_task.parameters = json.dumps({})
                    logger.warning(f"Failed to serialize parameters for task {task.task_id}: {str(json_error)}")
                    
                existing_task.error_message = task.error_message
                existing_task.fail_count = getattr(task, 'fail_count', 0)
            else:
                # 创建新任务数据
                db_task = TaskModel(
                    id=task.task_id,
                    task_type=task.task_type,
                    priority=task.priority.value,
                    status=task.status.value,
                    progress=task.progress,
                    created_at=task.created_at,
                    started_at=task.started_at,
                    completed_at=task.completed_at,
                    result=json.dumps(task.result) if task.result is not None else None,
                    error_message=task.error_message,
                    parameters=json.dumps(task.parameters) if task.parameters else None,
                    fail_count=getattr(task, 'fail_count', 0)
                )
                self.db_session.add(db_task)
            
            # 提交事务
            self.db_session.commit()
            logger.debug(f"Task {task.task_id} saved to database successfully")
        except Exception as e:
            error_msg = f"Failed to save task {task.task_id} to database: {str(e)}"
            logger.error(error_msg)
            # 回滚事务
            try:
                self.db_session.rollback()
            except Exception as rollback_error:
                logger.error(f"Failed to rollback transaction: {str(rollback_error)}")
                # 重新初始化数据库会话
                self._init_db_session()
            # 记录错误但不抛出异常，避免任务执行中断
    
    def _update_task_in_db(self, task: BaseTask) -> None:
        """更新数据库中的任务"""
        try:
            db_task = self.db_session.query(TaskModel).filter(TaskModel.id == task.task_id).first()
            if db_task:
                db_task.status = task.status.value
                db_task.progress = task.progress
                db_task.started_at = task.started_at
                db_task.completed_at = task.completed_at
                db_task.result = json.dumps(task.result) if task.result is not None else None
                db_task.error_message = task.error_message
                self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            # 记录错误但不抛出异常，避免任务执行中断
            print(f"Failed to update task in database: {str(e)}")
    
    def _load_task_from_db(self, task_id: str) -> Optional[BaseTask]:
        """从数据库加载任务"""
        try:
            db_task = self.db_session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if db_task:
                # 通过TaskFactory创建任务实例
                priority_value = TaskPriority[db_task.priority.upper()].value if db_task.priority else TaskPriority.MEDIUM.value
                task = TaskFactory.create_task(
                    db_task.task_type,
                    task_id=db_task.id,
                    priority=TaskPriority(priority_value)
                )
                
                # 设置任务属性
                task.status = TaskStatus(db_task.status)
                task.progress = db_task.progress
                task.created_at = db_task.created_at
                task.started_at = db_task.started_at
                task.completed_at = db_task.completed_at
                
                # 反序列化结果和参数
                if db_task.result:
                    try:
                        task.result = json.loads(db_task.result)
                    except (json.JSONDecodeError, TypeError):
                        task.result = db_task.result
                
                task.error_message = db_task.error_message
                
                if db_task.parameters:
                    try:
                        task.parameters = json.loads(db_task.parameters)
                    except (json.JSONDecodeError, TypeError):
                        task.parameters = {}
                
                self.tasks[task_id] = task
                return task
            return None
        except Exception as e:
            print(f"Failed to load task from database: {str(e)}")
            return None
    
    def _load_tasks_from_db_by_status(self, status: TaskStatus) -> list[BaseTask]:
        """从数据库加载指定状态的任务"""
        try:
            db_tasks = self.db_session.query(TaskModel).filter(TaskModel.status == status.value).all()
            tasks = []
            for db_task in db_tasks:
                if db_task.id not in self.tasks:
                    task = TaskFactory.create_task(
                        db_task.task_type,
                        task_id=db_task.id,
                        priority=TaskPriority(db_task.priority)
                    )
                    task.status = TaskStatus(db_task.status)
                    task.progress = db_task.progress
                    task.created_at = db_task.created_at
                    task.started_at = db_task.started_at
                    task.completed_at = db_task.completed_at
                    task.result = db_task.result
                    task.error = db_task.error
                    tasks.append(task)
            return tasks
        except Exception as e:
            raise TaskError(
                message=f"Failed to load tasks by status from database: {str(e)}",
                error_code="DB_LOAD_ERROR",
                details={"status": status.value}
            )
    
    def _load_all_tasks_from_db(self) -> list[BaseTask]:
        """从数据库加载所有任务"""
        try:
            db_tasks = self.db_session.query(TaskModel).all()
            tasks = []
            for db_task in db_tasks:
                if db_task.id not in self.tasks:
                    task = TaskFactory.create_task(
                        db_task.task_type,
                        task_id=db_task.id,
                        priority=TaskPriority(db_task.priority)
                    )
                    task.status = TaskStatus(db_task.status)
                    task.progress = db_task.progress
                    task.created_at = db_task.created_at
                    task.started_at = db_task.started_at
                    task.completed_at = db_task.completed_at
                    task.result = db_task.result
                    task.error = db_task.error
                    tasks.append(task)
            return tasks
        except Exception as e:
            raise TaskError(
                message=f"Failed to load all tasks from database: {str(e)}",
                error_code="DB_LOAD_ERROR"
            )
    
    def _delete_task_from_db(self, task_id: str) -> None:
        """从数据库删除任务"""
        try:
            db_task = self.db_session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if db_task:
                self.db_session.delete(db_task)
                self.db_session.commit()
        except Exception as e:
            self.db_session.rollback()
            raise TaskError(
                message=f"Failed to delete task from database: {str(e)}",
                error_code="DB_DELETE_ERROR",
                details={"task_id": task_id}
            )
    
    def _init_workers(self) -> None:
        """初始化工作线程，确保线程安全"""
        with self.lock:
            # 清除现有线程（如果有）
            self.workers = []
            
            for i in range(self.max_workers):
                try:
                    worker = threading.Thread(target=self._worker_loop, daemon=True, name=f"task-worker-{i}")
                    worker.start()
                    self.workers.append(worker)
                    logger.debug(f"Worker thread {i} started")
                except Exception as e:
                    logger.error(f"Failed to start worker thread {i}: {str(e)}")
            
            logger.info(f"Initialized {len(self.workers)} out of {self.max_workers} requested worker threads")
    
    def _worker_loop(self) -> None:
        """工作线程循环处理任务，增强异常处理"""
        thread_id = threading.get_ident()
        thread_name = threading.current_thread().name
        logger.info(f"Worker thread {thread_name} (ID: {thread_id}) started")
        
        while not self.stop_event.is_set():
            try:
                # 获取下一个任务ID
                priority, task_id = self._get_next_task_id()
                if task_id:
                    with self.lock:
                        # 检查任务是否存在且未被其他线程处理
                        if task_id not in self.tasks:
                            logger.warning(f"Task {task_id} not found in memory, skipping")
                            continue
                        task = self.tasks[task_id]
                        # 检查任务状态，避免重复处理
                        if task.status != TaskStatus.PENDING:
                            logger.debug(f"Task {task_id} has status {task.status.value}, skipping")
                            continue
                        # 标记任务为运行中
                        self._update_task_status(task, TaskStatus.RUNNING)
                        logger.info(f"Worker {thread_name} processing task {task_id}")
                    
                    try:
                        # 执行任务并处理结果
                        result = self._execute_task_with_timeout(task)
                        with self.lock:
                            self._update_task_result(task, result)
                        logger.info(f"Worker {thread_name} completed task {task_id}, success={result.success}")
                    except Exception as e:
                        with self.lock:
                            self._handle_task_error(task, e)
                        logger.error(f"Worker {thread_name} error processing task {task_id}: {str(e)}")
            except Exception as e:
                logger.error(f"Worker {thread_name} loop error: {str(e)}")
            
            # 短暂休眠避免CPU占用过高
            time.sleep(0.1)
        
        logger.info(f"Worker thread {thread_name} (ID: {thread_id}) stopped")
    
    def _get_next_task_id(self) -> tuple:
        """从优先级队列获取下一个任务ID"""
        try:
            # 使用阻塞式获取，但设置超时以便定期检查停止事件
            priority, task_id = self.task_queue.get(timeout=1.0)
            # 标记任务已完成处理（从队列中移除）
            self.task_queue.task_done()
            return (priority, task_id)
        except Empty:
            return (None, None)
        except Exception:
            return (None, None)
    
    def _get_task(self, task_id: str) -> Optional[BaseTask]:
        """获取任务实例"""
        # 优先从内存中获取
        if task_id in self.tasks:
            return self.tasks[task_id]
        # 从数据库加载
        return self._load_task_from_db(task_id)
    
    def _update_task_status(self, task: BaseTask, status: TaskStatus) -> None:
        """更新任务状态"""
        task.status = status
        # 更新数据库
        self._update_task_in_db(task)
    
    def _execute_task_with_timeout(self, task: BaseTask) -> TaskResult:
        """带超时控制的任务执行"""
        from concurrent.futures import ThreadPoolExecutor, TimeoutError
        
        # 获取任务特定的超时设置（如果有）
        timeout = getattr(task, 'timeout', self.default_timeout)
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(task.execute)
            try:
                return future.result(timeout=timeout)
            except TimeoutError:
                error_msg = f"Task execution timed out after {timeout} seconds"
                print(f"Task {task.task_id} timeout: {error_msg}")
                return TaskResult(success=False, error_message=error_msg)
    
    def _update_task_result(self, task: BaseTask, result: TaskResult) -> None:
        """更新任务结果，确保结果正确保存并处理异常情况"""
        try:
            # 更新任务状态和结果
            task.complete(result)
            logger.info(f"Task {task.task_id} completed with status: {'success' if result.success else 'failure'}")
            
            # 尝试保存任务状态到数据库
            retry_count = 0
            max_db_retries = 3
            db_error = None
            
            while retry_count < max_db_retries:
                try:
                    self._update_task_in_db(task)
                    logger.debug(f"Task {task.task_id} result saved to database (attempt {retry_count + 1})")
                    db_error = None
                    break
                except Exception as e:
                    retry_count += 1
                    db_error = str(e)
                    logger.warning(f"Failed to save task {task.task_id} result to database (attempt {retry_count}): {db_error}")
                    if retry_count < max_db_retries:
                        # 短暂休眠后重试
                        time.sleep(0.5)
                    # 尝试重新初始化数据库会话
                    self._init_db_session()
            
            if db_error:
                logger.error(f"Failed to save task {task.task_id} result after {max_db_retries} attempts: {db_error}")
            
            # 更新内存中的任务状态
            with self.lock:
                if task.task_id in self.tasks:
                    self.tasks[task.task_id] = task
            
        except Exception as e:
            logger.error(f"Error updating task {task.task_id} result: {str(e)}")
            # 即使保存失败，也尝试标记任务为失败状态
            try:
                task.status = TaskStatus.FAILED
                task.error_message = f"Failed to update task result: {str(e)}"
                self._update_task_in_db(task)
            except:
                pass
    
    def _handle_task_error(self, task: BaseTask, error: Exception) -> None:
        """处理任务执行错误，增强错误处理和重试逻辑"""
        try:
            # 记录错误信息
            error_message = f"{str(error)} (Exception type: {type(error).__name__})"
            logger.error(f"Task {task.task_id} execution error: {error_message}")
            
            # 更新任务状态
            task.status = TaskStatus.FAILED
            task.error_message = error_message
            task.completed_at = datetime.utcnow()
            
            # 增加失败计数
            if not hasattr(task, 'fail_count'):
                task.fail_count = 0
            task.fail_count += 1
            
            # 尝试保存错误状态到数据库
            try:
                self._update_task_in_db(task)
                logger.debug(f"Task {task.task_id} error status saved to database")
            except Exception as db_error:
                logger.warning(f"Failed to save error status for task {task.task_id}: {str(db_error)}")
                # 尝试重新初始化数据库会话
                self._init_db_session()
                # 尝试使用save_task_to_db作为备选
                try:
                    self._save_task_to_db(task)
                except:
                    pass
            
            # 更新内存中的任务状态
            with self.lock:
                if task.task_id in self.tasks:
                    self.tasks[task.task_id] = task
            
            # 尝试重试任务（如果配置了重试）
            if task.fail_count <= self.max_retries:
                logger.info(f"Task {task.task_id} will retry ({task.fail_count}/{self.max_retries})...")
                # 延迟重试
                threading.Timer(
                    self.retry_delay, 
                    self._retry_task, 
                    args=[task]
                ).start()
            else:
                logger.warning(f"Task {task.task_id} reached maximum retry attempts ({self.max_retries})")
                
        except Exception as e:
            logger.critical(f"Critical error handling task {task.task_id} error: {str(e)}")

    def _retry_task(self, task: BaseTask) -> None:
        """重试任务"""
        if self.stop_event.is_set():
            return
            
        with self.lock:
            # 重新设置任务状态为待处理
            task.status = TaskStatus.PENDING
            task.started_at = None
            task.completed_at = None
            
            # 保存到数据库
            self._save_task_to_db(task)
            
            # 重新加入队列
            self.task_queue.put((task.priority.value, task.task_id))
            print(f"Task {task.task_id} retried")
    
    def _init_db_session(self) -> None:
        """初始化数据库会话"""
        try:
            if self.db_session and self.db_session.is_active:
                self.db_session.close()
            self.db_session = SessionLocal()
            logger.info("Database session initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database session: {str(e)}")
            self.db_session = None
    
    def stop(self) -> None:
        """停止任务管理器"""
        logger.info("Stopping task manager...")
        
        # 设置停止标志
        self.stop_event.set()
        
        # 等待所有工作线程完成
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=5.0)
        
        # 清理资源
        if self.db_session:
            try:
                self.db_session.close()
                logger.info("Database session closed successfully")
            except Exception as e:
                logger.error(f"Error closing database session: {str(e)}")
            self.db_session = None
        
        logger.info("Task manager stopped")
        
    def __del__(self):
        """析构函数，调用stop方法关闭资源"""
        self.stop()


# 创建全局任务管理器实例
global_task_manager = TaskManager()


# 定义装饰器用于注册任务

def register_task(task_type: str):
    """任务注册装饰器"""
    def decorator(task_class):
        TaskFactory.register_task(task_type, task_class)
        return task_class
    return decorator
