// Git MCP 服务使用工具
// 提供与已配置的git mcp服务交互的方法

/**
 * Git MCP服务客户端
 * 用于与vite.config.ts中配置的git-service进行交互
 */
export class GitMcpService {
  private static readonly MCP_SERVICE_URL = '/api/mcp/git-service';

  /**
   * 执行git命令
   * @param command git子命令（如clone, pull, push等）
   * @param args 命令参数数组
   * @returns 命令执行结果
   */
  static async executeGitCommand(command: string, args: string[] = []): Promise<{
    success: boolean;
    output: string;
    error?: string;
  }> {
    try {
      // 通过MCP服务执行git命令
      const response = await fetch(this.MCP_SERVICE_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          command,
          args
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      return {
        success: false,
        output: '',
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  /**
   * 克隆仓库
   * @param repoUrl 仓库URL
   * @param localPath 本地路径
   * @returns 命令执行结果
   */
  static async clone(repoUrl: string, localPath: string): Promise<{
    success: boolean;
    output: string;
    error?: string;
  }> {
    return this.executeGitCommand('clone', [repoUrl, localPath]);
  }

  /**
   * 拉取最新代码
   * @param localPath 本地仓库路径
   * @param branch 分支名
   * @returns 命令执行结果
   */
  static async pull(localPath: string, branch: string = 'main'): Promise<{
    success: boolean;
    output: string;
    error?: string;
  }> {
    return this.executeGitCommand('pull', ['origin', branch], { cwd: localPath });
  }

  /**
   * 提交更改
   * @param localPath 本地仓库路径
   * @param message 提交信息
   * @returns 命令执行结果
   */
  static async commit(localPath: string, message: string): Promise<{
    success: boolean;
    output: string;
    error?: string;
  }> {
    return this.executeGitCommand('commit', ['-m', message], { cwd: localPath });
  }

  /**
   * 推送代码
   * @param localPath 本地仓库路径
   * @param branch 分支名
   * @returns 命令执行结果
   */
  static async push(localPath: string, branch: string = 'main'): Promise<{
    success: boolean;
    output: string;
    error?: string;
  }> {
    return this.executeGitCommand('push', ['origin', branch], { cwd: localPath });
  }

  /**
   * 获取仓库状态
   * @param localPath 本地仓库路径
   * @returns 命令执行结果
   */
  static async status(localPath: string): Promise<{
    success: boolean;
    output: string;
    error?: string;
  }> {
    return this.executeGitCommand('status', [], { cwd: localPath });
  }

  /**
   * 辅助方法：带工作目录的命令执行
   * @param command git命令
   * @param args 参数
   * @param options 选项
   * @returns 命令执行结果
   */
  private static async executeGitCommand(
    command: string, 
    args: string[], 
    options?: { cwd?: string }
  ): Promise<{
    success: boolean;
    output: string;
    error?: string;
  }> {
    return this.executeGitCommand(command, [...args, ...(options?.cwd ? [`--working-dir=${options.cwd}`] : [])]);
  }
}

/**
 * 示例用法
 * 
 * // 在组件中使用Git MCP服务
 * import { GitMcpService } from '@/utils/gitMcpService';
 * 
 * // 克隆仓库
 * const result = await GitMcpService.clone('git://localhost/myrepo.git', './myrepo');
 * if (result.success) {
 *   console.log('Clone successful:', result.output);
 * } else {
 *   console.error('Clone failed:', result.error);
 * }
 * 
 * // 检查仓库状态
 * const statusResult = await GitMcpService.status('./myrepo');
 * console.log('Repository status:', statusResult.output);
 */
