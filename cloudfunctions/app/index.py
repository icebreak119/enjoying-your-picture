import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def main_handler(event, context):
    from app import app

    # 处理请求
    from flask import request, make_response
    from werkzeug.datastructures import Headers

    # 解析event为Flask请求
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET')
    headers = Headers(event.get('headers', {}))
    query_string = event.get('queryStringParameters', {})
    body = event.get('body', '')

    # 创建Flask测试请求
    with app.test_request_context(
            path=path,
            method=method,
            headers=headers,
            query_string=query_string,
            data=body
    ):
        from werkzeug.test import Client
        from werkzeug.wrappers import Response

        client = Client(app, Response)
        response = client.open(path, method=method, headers=dict(headers))

        return {
            'statusCode': response.status_code,
            'headers': dict(response.headers),
            'body': response.get_data(as_text=True)
        }