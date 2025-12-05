"""
Vercel Serverless 入口文件
注意：这不是完整的 app.py，而是适配 Vercel 的入口
"""

import sys
import os

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 导入 Flask 应用
from app import app

# Vercel 需要的 WSGI 应用对象
# 注意：这里必须是 'application' 而不是 'app'
application = app

# 简化的处理函数，避免冷启动慢
def handler(event, context):
    """Serverless 处理函数"""
    return application