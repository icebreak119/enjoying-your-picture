import requests
import time
import sys

def test_flask_app():
    """测试Flask应用"""
    base_url = "http://localhost:5000"
    
    print("测试Flask应用...")
    print("=" * 50)
    
    # 测试首页
    print("1. 测试首页...")
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("   ✅ 首页正常")
        else:
            print(f"   ❌ 首页异常: 状态码 {response.status_code}")
    except Exception as e:
        print(f"   ❌ 无法连接到首页: {e}")
        return False
    
    # 等待应用完全启动
    time.sleep(1)
    
    # 测试搜索功能
    print("\n2. 测试搜索功能...")
    
    test_cases = [
        ("landscape", "风景图片"),
        ("admin", "admin用户上传的图片"),
        ("test", "test用户上传的图片"),
        ("", "空搜索"),
        ("nonexistent123", "不存在的关键词")
    ]
    
    for query, description in test_cases:
        print(f"   搜索 '{query}' ({description})...")
        try:
            url = f"{base_url}/search?q={query}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                if query and "没有找到相关图片" in response.text:
                    print(f"      ✅ 正确显示: 无结果")
                elif not query and "请输入搜索关键词" in response.text:
                    print(f"      ✅ 正确显示: 请输入关键词")
                elif query and ("搜索结果" in response.text or "找到" in response.text):
                    print(f"      ✅ 搜索成功")
                else:
                    print(f"      ⚠️  未知响应")
            else:
                print(f"      ❌ HTTP错误: {response.status_code}")
        except Exception as e:
            print(f"      ❌ 请求失败: {e}")
    
    print("\n3. 测试数据库连接...")
    try:
        # 测试数据库连接状态
        response = requests.get(base_url, timeout=5)
        if "数据库" in response.text:
            print("   ✅ 数据库连接正常")
        else:
            print("   ⚠️  无法确认数据库状态")
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
    
    print("\n" + "=" * 50)
    print("测试完成！")
    print("\n提示：")
    print("1. 确保Flask应用正在运行（python app.py）")
    print("2. 如果端口不是5000，请修改测试脚本中的base_url")
    print("3. 如果遇到数据库错误，请检查数据库配置")
    return True

if __name__ == "__main__":
    # 检查参数
    if len(sys.argv) > 1:
        port = sys.argv[1]
        print(f"使用端口: {port}")
    else:
        port = "5000"
    
    print(f"Flask应用测试脚本")
    print(f"目标地址: http://localhost:{port}")
    print("=" * 50)
    
    test_flask_app()
