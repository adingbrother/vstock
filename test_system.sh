#!/bin/bash

# 量化投研平台系统测试脚本
echo "===== 量化投研平台系统测试 ===="

# 测试后端API健康检查
echo "\n测试后端健康检查..."
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "✅ 后端健康检查通过"
    echo "后端API响应:"
    curl -s http://localhost:8000/api/v1/health
else
    echo "❌ 后端服务可能未运行或无法访问"
    echo "请确保后端服务正在运行:"
    echo "  cd /Users/wangxx/Desktop/python3/vstock"
    echo "  source .venv/bin/activate"
    echo "  python3 -m uvicorn quant_web.main:app --host 0.0.0.0 --port 8000 --reload"
fi

# 测试前端页面可访问性
echo "\n测试前端页面可访问性..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/ | grep -q "200"; then
    echo "✅ 前端页面可正常访问"
    echo "访问地址: http://localhost:5173/"
else
    echo "❌ 前端服务可能未运行或无法访问"
    echo "请确保前端服务正在运行:"
    echo "  cd /Users/wangxx/Desktop/python3/vstock/frontend"
    echo "  npm run dev"
fi

echo "\n测试完成！请访问 http://localhost:5173/ 开始使用量化投研平台。"
echo "详细使用说明请参考: /Users/wangxx/Desktop/python3/vstock/LOCAL_RUN_GUIDE.md"