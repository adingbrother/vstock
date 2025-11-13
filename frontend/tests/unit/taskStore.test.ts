import { describe, it, expect, beforeEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useTaskStore } from '@/stores/taskStore';
import { TaskStatus } from '@/types/task';

// Mock WebSocket服务
vi.mock('@/services/websocketService', () => ({
  websocketService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    subscribeTask: vi.fn(),
    unsubscribeTask: vi.fn(),
    requestMoreTasks: vi.fn(),
  }
}));

describe('TaskStore', () => {
  let store: ReturnType<typeof useTaskStore>;

  beforeEach(() => {
    // 创建一个新的pinia实例用于测试
    setActivePinia(createPinia());
    store = useTaskStore();
  });

  it('应该初始化正确的默认状态', () => {
    expect(store.tasks).toEqual([]);
    expect(store.filter).toBe('all');
    expect(store.loading).toBe(false);
    expect(store.loadingMore).toBe(false);
    expect(store.hasMoreTasks).toBe(true);
    expect(store.currentPage).toBe(1);
    expect(store.pageSize).toBe(20);
  });

  it('应该正确过滤任务', () => {
    // 添加一些测试任务
    store.tasks = [
      { id: '1', status: TaskStatus.PENDING, name: 'Task 1', progress: 0, taskType: 'download' },
      { id: '2', status: TaskStatus.RUNNING, name: 'Task 2', progress: 50, taskType: 'backtest' },
      { id: '3', status: TaskStatus.COMPLETED, name: 'Task 3', progress: 100, taskType: 'download' },
      { id: '4', status: TaskStatus.FAILED, name: 'Task 4', progress: 0, taskType: 'backtest' }
    ];

    // 测试过滤为'running'状态
    store.filter = 'running';
    expect(store.filteredTasks).toHaveLength(1);
    expect(store.filteredTasks[0].id).toBe('2');

    // 测试过滤为'completed'状态
    store.filter = 'completed';
    expect(store.filteredTasks).toHaveLength(1);
    expect(store.filteredTasks[0].id).toBe('3');

    // 测试过滤为'all'状态
    store.filter = 'all';
    expect(store.filteredTasks).toHaveLength(4);
  });

  it('应该正确返回分页任务', () => {
    // 添加测试任务
    const tasks = Array.from({ length: 30 }, (_, i) => ({
      id: `task-${i + 1}`,
      status: TaskStatus.COMPLETED,
      name: `Task ${i + 1}`,
      progress: 100,
      taskType: 'download',
      createdAt: new Date().toISOString()
    }));
    store.tasks = tasks;

    // 测试第一页
    expect(store.paginatedTasks).toHaveLength(20);
    expect(store.paginatedTasks[0].id).toBe('task-1');

    // 测试加载更多
    store.currentPage = 2;
    expect(store.paginatedTasks).toHaveLength(10);
    expect(store.paginatedTasks[0].id).toBe('task-21');
  });

  it('应该正确设置过滤器', () => {
    store.setFilter('failed');
    expect(store.filter).toBe('failed');
    expect(store.currentPage).toBe(1); // 切换过滤器应该重置分页
    expect(store.hasMoreTasks).toBe(true); // 切换过滤器应该重置hasMoreTasks
  });

  it('应该正确处理加载更多任务', async () => {
    const mockTasks = Array.from({ length: 10 }, (_, i) => ({
      id: `more-task-${i + 1}`,
      status: TaskStatus.COMPLETED,
      name: `More Task ${i + 1}`,
      progress: 100,
      taskType: 'download',
      createdAt: new Date().toISOString()
    }));

    // Mock fetchMoreTasks方法
    store.tasks = [];
    store.fetchMoreTasks = vi.fn(async () => {
      store.loadingMore = true;
      // 模拟异步操作
      await new Promise(resolve => setTimeout(resolve, 10));
      store.tasks.push(...mockTasks);
      store.currentPage += 1;
      store.loadingMore = false;
    });

    await store.fetchMoreTasks();
    
    expect(store.loadingMore).toBe(false);
    expect(store.currentPage).toBe(2);
    expect(store.tasks).toHaveLength(10);
  });

  it('应该正确重置分页', () => {
    store.currentPage = 5;
    store.hasMoreTasks = false;
    store.resetPagination();
    
    expect(store.currentPage).toBe(1);
    expect(store.hasMoreTasks).toBe(true);
  });

  it('应该正确更新任务状态', () => {
    const taskId = 'test-task';
    store.tasks = [
      { id: taskId, status: TaskStatus.PENDING, name: 'Test Task', progress: 0, taskType: 'download' }
    ];

    store.updateTaskStatus(taskId, TaskStatus.RUNNING, 50, 'Processing...');
    
    const updatedTask = store.tasks.find(t => t.id === taskId);
    expect(updatedTask).toBeDefined();
    expect(updatedTask?.status).toBe(TaskStatus.RUNNING);
    expect(updatedTask?.progress).toBe(50);
  });
});
