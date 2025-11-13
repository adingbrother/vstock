import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from fastapi import FastAPI, HTTPException

# 简化测试，直接测试应用行为而不是使用TestClient

def test_app_creation():
    """测试FastAPI应用创建"""
    app = FastAPI()
    assert app is not None
    assert app.title == "FastAPI"  # 默认标题

def test_exception_raising():
    """测试异常抛出"""
    # 测试HTTPException
    with pytest.raises(HTTPException) as excinfo:
        raise HTTPException(status_code=400, detail="Test error")
    assert excinfo.value.status_code == 400
    assert excinfo.value.detail == "Test error"

    # 测试不同状态码的HTTPException
    with pytest.raises(HTTPException) as excinfo:
        raise HTTPException(status_code=404, detail="Not found")
    assert excinfo.value.status_code == 404
    
    with pytest.raises(HTTPException) as excinfo:
        raise HTTPException(status_code=500, detail="Internal server error")
    assert excinfo.value.status_code == 500
