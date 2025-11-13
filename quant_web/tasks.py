from celery import Celery
import os
from quant_web.core.task_manager import (
    BaseTask, TaskResult, register_task, TaskPriority,
    global_task_manager
)

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_app = Celery("quant_web_tasks", broker=redis_url, backend=redis_url)


@celery_app.task
def ping(x):
    return f"pong {x}"


@register_task("download_stocks")
class DownloadStocksTask(BaseTask):
    """股票下载任务类"""
    
    def __init__(self, task_id: str = None, stock_list: list = None):
        super().__init__(task_id=task_id, priority=TaskPriority.HIGH)
        self.stock_list = stock_list or []
        self.redis_client = None
        self.session = None
    
    def execute(self) -> TaskResult:
        """执行股票下载任务"""
        import time
        import uuid
        import redis
        import json
        from models.database import SessionLocal
        from quant_web.models.models import DataDownloadLog
        
        try:
            # 初始化Redis客户端
            try:
                self.redis_client = redis.from_url(
                    os.getenv("REDIS_URL", "redis://localhost:6379/0")
                )
            except Exception:
                self.redis_client = None
            
            # 初始化数据库会话
            self.session = SessionLocal()
            
            # 开始任务
            self.start()
            
            # 处理每个股票
            for i, s in enumerate(self.stock_list):
                # 模拟工作
                time.sleep(1)
                
                # 添加下载日志
                log = DataDownloadLog(
                    id=str(uuid.uuid4()),
                    task_id=self.task_id,
                    ts_code=s,
                    status='downloaded',
                    message='ok'
                )
                self.session.add(log)
                self.session.commit()
                
                # 更新进度
                progress = (i + 1) / len(self.stock_list)
                self.update_progress(progress)
                
                # 发布进度消息
                self._publish_progress(s, "downloaded")
            
            # 完成任务
            result = TaskResult(success=True, data={'status': 'done', 'task_id': self.task_id})
            self.complete(result)
            return result
            
        except Exception as e:
            if self.session:
                self.session.rollback()
            error_result = TaskResult(success=False, error_message=str(e))
            self.complete(error_result)
            return error_result
            
        finally:
            if self.session:
                self.session.close()
    
    def _publish_progress(self, ts_code: str, message: str) -> None:
        """发布进度消息"""
        msg = {
            "type": "progress", 
            "task_id": self.task_id, 
            "ts_code": ts_code, 
            "message": message,
            "progress": self.progress
        }
        try:
            if self.redis_client:
                self.redis_client.publish(f"task:{self.task_id}", json.dumps(msg))
        except Exception:
            # 忽略发布错误
            pass


@celery_app.task(bind=True)
def download_stocks(self, task_id: str, stock_list: list):
    """Celery任务入口，使用DownloadStocksTask类"""
    from quant_web.core.task_manager import TaskFactory
    
    # 创建任务实例
    task = TaskFactory.create_task("download_stocks", task_id=task_id, stock_list=stock_list)
    
    # 添加到全局任务管理器
    global_task_manager.add_task(task)
    
    # 执行任务
    result = task.execute()
    
    # 返回结果供Celery使用
    if result.success:
        return result.data
    else:
        # Celery会将异常信息包装，这里返回错误字典
        return {'status': 'error', 'message': result.error_message}
