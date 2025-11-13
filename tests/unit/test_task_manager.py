import pytest
import asyncio
from quant_web.core.task_manager import TaskStatus, TaskPriority, BaseTask, TaskFactory
from quant_web.state import TASK_QUEUES


class TestTask(BaseTask):
    """测试用的任务类"""
    def __init__(self, task_id, name="Test Task", description="Test Description"):
        super().__init__(task_id, name, description)
        self.progress_value = 0
        
    async def execute(self):
        """模拟任务执行过程"""
        try:
            # 模拟任务进度更新
            for i in range(1, 101):
                self.progress_value = i
                await self.update_progress(i, f"Progress: {i}%")
                await asyncio.sleep(0.01)  # 模拟处理时间
            
            # 设置任务完成
            self.status = TaskStatus.COMPLETED
            return {"result": "success", "message": "Task completed successfully"}
            
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = str(e)
            raise


@pytest.mark.asyncio
async def test_task_execution():
    """测试任务执行过程"""
    task_id = "test-task-123"
    task = TestTask(task_id)
    
    # 初始化检查
    assert task.task_id == task_id
    assert task.status == TaskStatus.PENDING
    assert task.progress == 0
    
    # 执行任务
    result = await task.execute()
    
    # 验证结果
    assert task.status == TaskStatus.COMPLETED
    assert task.progress == 100
    assert result["result"] == "success"


@pytest.mark.asyncio
async def test_task_progress_updates():
    """测试任务进度更新"""
    task_id = "test-task-progress"
    task = TestTask(task_id)
    
    # 创建任务队列以捕获进度更新
    if task_id not in TASK_QUEUES:
        TASK_QUEUES[task_id] = asyncio.Queue()
    
    # 在后台执行任务
    task_future = asyncio.create_task(task.execute())
    
    # 收集进度更新
    progress_updates = []
    try:
        # 收集一些进度更新（不等待完成以节省时间）
        for _ in range(5):
            update = await asyncio.wait_for(TASK_QUEUES[task_id].get(), timeout=1.0)
            if update["type"] == "progress":
                progress_updates.append(update)
    except asyncio.TimeoutError:
        pass
    finally:
        # 取消任务
        task_future.cancel()
        # 清理队列
        if task_id in TASK_QUEUES:
            del TASK_QUEUES[task_id]
    
    # 验证至少收到了一些进度更新
    assert len(progress_updates) > 0
    # 验证进度是递增的
    progress_values = [update["progress"] for update in progress_updates]
    assert sorted(progress_values) == progress_values


@pytest.mark.asyncio
async def test_task_failure():
    """测试任务失败情况"""
    class FailingTask(BaseTask):
        async def execute(self):
            raise ValueError("Test task failure")
    
    task_id = "test-task-fail"
    task = FailingTask(task_id)
    
    # 执行任务并验证异常
    with pytest.raises(ValueError, match="Test task failure"):
        await task.execute()
    
    # 验证任务状态
    assert task.status == TaskStatus.FAILED
    assert task.error == "Test task failure"


@pytest.mark.asyncio
async def test_task_factory():
    """测试任务工厂功能"""
    # 注册测试任务类型
    TaskFactory.register("test_task", TestTask)
    
    # 使用工厂创建任务
    task_id = "factory-test-task"
    task = TaskFactory.create(
        "test_task",
        task_id,
        name="Factory Test Task",
        description="Task created by factory"
    )
    
    # 验证任务创建成功
    assert isinstance(task, TestTask)
    assert task.task_id == task_id
    assert task.name == "Factory Test Task"
    assert task.description == "Task created by factory"
    
    # 测试未知任务类型
    with pytest.raises(ValueError, match="Unknown task type"):
        TaskFactory.create("unknown_task_type", "unknown-id")


if __name__ == "__main__":
    pytest.main([__file__])
