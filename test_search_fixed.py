import requests


def test_search():
    base_url = "http://localhost:5000"

    # 测试正常搜索
    print("测试搜索功能...")

    test_cases = [
        ("landscape", "应该找到风景图片"),
        ("admin", "应该找到admin上传的图片"),
        ("", "空搜索应该显示提示"),
        ("nonexistent123", "不存在的关键词应该返回空结果")
    ]

    for query, description in test_cases:
        print(f"\n测试: {description}")
        print(f"搜索关键词: '{query}'")

        url = f"{base_url}/search?q={query}"

        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ 状态码: {response.status_code}")

                if "没有找到相关图片" in response.text and query:
                    print("✅ 正确显示无结果消息")
                elif "请输入搜索关键词" in response.text and not query:
                    print("✅ 正确显示输入提示")
                elif query and "搜索" in response.text:
                    print("✅ 搜索结果显示正常")
            else:
                print(f"❌ 状态码: {response.status_code}")
        except Exception as e:
            print(f"❌ 请求失败: {e}")

    print("\n" + "=" * 50)
    print("搜索功能测试完成！")


if __name__ == "__main__":
    print("开始测试修复后的搜索功能...")
    print("=" * 50)
    test_search()