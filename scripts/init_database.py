#!/usr/bin/env python3
"""数据库初始化脚本"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import init_db

def main():
    print("开始初始化数据库...")
    try:
        # 确保data目录存在
        os.makedirs("data", exist_ok=True)
        print("数据目录检查完成")
        
        # 导入模型以注册到Base.metadata
        # 模型将在init_db函数内部导入
        print("模型导入成功")
        
        # 初始化数据库表
        init_db()
        print("数据库表创建成功！")
        
        print("数据库初始化完成！")
    except Exception as e:
        print(f"数据库初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
