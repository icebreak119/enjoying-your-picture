"""
修复搜索功能的脚本
"""

import os
import shutil
from datetime import datetime

def backup_file(filepath):
    """备份文件"""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{filepath}.backup_{timestamp}"
        shutil.copy2(filepath, backup_path)
        print(f"✅ 已备份: {filepath} -> {backup_path}")
        return backup_path
    return None

def fix_app_py():
    """修复app.py中的搜索函数"""
    app_py_path = "app.py"
    
    # 读取文件内容
    with open(app_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    backup_file(app_py_path)
    
    # 查找搜索函数
    if "@app.route('/search')" in content:
        print("✅ 找到search路由")
        
        # 用正确的搜索函数替换
        new_search_function = '''
@app.route('/search')
def search():
    """搜索功能 - 多字段搜索（标题、描述、用户名）和分页"""
    query_text = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 12

    # 创建默认结果
    default_result = {
        'items': [],
        'page': 1,
        'pages': 1,
        'total': 0,
        'per_page': per_page
    }
    
    if not query_text:
        return render_template('search.html', 
                             query=query_text, 
                             search_result=default_result)

    try:
        search_param = f"%{query_text}%"
        offset = (page - 1) * per_page

        # 搜索查询
        search_query = """
            SELECT i.*, u.username 
            FROM images i 
            LEFT JOIN users u ON i.user_id = u.id 
            WHERE (i.title LIKE %s OR i.description LIKE %s OR u.username LIKE %s)
            ORDER BY i.upload_time DESC
            LIMIT %s, %s
        """

        params = (search_param, search_param, search_param, offset, per_page)
        results = execute_query(search_query, params, fetch_all=True)

        images_list = []
        if results:
            for row in results:
                file_path = row['file_path']
                if file_path.startswith('/'):
                    file_path = file_path[1:]

                thumbnail_path = row.get('thumbnail_path')
                if thumbnail_path and thumbnail_path.startswith('/'):
                    thumbnail_path = thumbnail_path[1:]

                image = {
                    'id': row['id'],
                    'filename': row['filename'],
                    'original_filename': row['original_name'],
                    'title': row['title'] or row['original_name'],
                    'description': row['description'] or '',
                    'upload_time': row.get('upload_time', datetime.now()),
                    'views': row.get('views', 0),
                    'likes': row.get('likes', 0),
                    'username': row['username'],
                    'file_path': file_path,
                    'thumbnail_path': thumbnail_path,
                    'author': {'username': row['username']}
                }
                images_list.append(image)

        # 获取总数
        count_query = """
            SELECT COUNT(*) as total 
            FROM images i 
            LEFT JOIN users u ON i.user_id = u.id 
            WHERE (i.title LIKE %s OR i.description LIKE %s OR u.username LIKE %s)
        """
        count_result = execute_query(count_query, (search_param, search_param, search_param), fetch_one=True)
        
        if count_result:
            total = count_result['total']
        else:
            total = 0

        # 计算总页数
        pages = math.ceil(total / per_page) if total > 0 else 1

        # 创建分页对象
        pagination_data = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': pages,
            'items': images_list
        }

        print(f"搜索成功: 关键词='{query_text}', 结果数={total}, 当前页={page}, 总页数={pages}")
        return render_template('search.html', query=query_text, search_result=pagination_data)

    except Exception as e:
        print(f"搜索失败: {e}")
        flash(f'搜索时发生错误: {str(e)}', 'danger')
        return render_template('search.html', 
                             query=query_text, 
                             search_result=default_result)
'''
        
        # 查找旧的search函数并替换
        start_marker = "@app.route('/search')"
        end_marker = "@app.errorhandler(404)"
        
        if start_marker in content and end_marker in content:
            # 提取search函数之前的内容
            before_search = content.split(start_marker)[0]
            # 提取search函数之后的内容
            after_search = content.split(end_marker)[1]
            after_search = end_marker + after_search
            
            # 构建新内容
            new_content = before_search + new_search_function + "\n\n" + after_search
            
            # 写入文件
            with open(app_py_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print("✅ 已修复app.py中的搜索函数")
            return True
        else:
            print("❌ 无法定位search函数")
            return False
    else:
        print("❌ 未找到search路由")
        return False

def fix_search_html():
    """修复search.html模板"""
    search_html_path = "templates/search.html"
    
    # 备份文件
    backup_file(search_html_path)
    
    # 创建新的search.html
    new_search_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>搜索 - 图片分享站</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
    <style>
        .card-img-container {
            height: 200px;
            overflow: hidden;
        }
        .card-img-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s;
        }
        .card-img-container img:hover {
            transform: scale(1.05);
        }
        .text-truncate-2 {
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }
    </style>
</head>
<body>
    <div class="container py-4">
        <h1 class="mb-4"><i class="bi bi-search"></i> 搜索图片</h1>
        
        <!-- 搜索框 -->
        <div class="row mb-4">
            <div class="col-md-8">
                <form action="/search" method="get">
                    <div class="input-group">
                        <input type="text" class="form-control" name="q" 
                               value="{{ query }}" placeholder="搜索图片标题、描述或作者...">
                        <button type="submit" class="btn btn-primary">
                            <i class="bi bi-search"></i> 搜索
                        </button>
                    </div>
                </form>
            </div>
        </div>
        
        <!-- 搜索结果 -->
        {% if query %}
            <div class="mb-4">
                <h4>搜索 "{{ query }}" 的结果：</h4>
                {% if search_result.total > 0 %}
                    <p class="text-muted">找到 {{ search_result.total }} 个结果</p>
                {% endif %}
            </div>
            
            {% if search_result.total > 0 %}
                <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-4">
                    {% for image in search_result.items %}
                    <div class="col">
                        <div class="card h-100 shadow-sm">
                            <div class="card-img-container">
                                <a href="/image/{{ image.id }}">
                                    {% if image.thumbnail_path %}
                                        <img src="{{ url_for('static', filename=image.thumbnail_path) }}" 
                                             alt="{{ image.title }}" class="card-img-top">
                                    {% else %}
                                        <img src="{{ url_for('static', filename=image.file_path) }}" 
                                             alt="{{ image.title }}" class="card-img-top">
                                    {% endif %}
                                </a>
                            </div>
                            <div class="card-body">
                                <h5 class="card-title">{{ image.title[:30] }}{% if image.title|length > 30 %}...{% endif %}</h5>
                                <p class="card-text text-truncate-2">
                                    {{ image.description[:80] if image.description else '暂无描述' }}
                                </p>
                                <div class="d-flex justify-content-between align-items-center">
                                    <small class="text-muted">
                                        <i class="bi bi-person"></i> {{ image.author.username if image.author else '未知' }}
                                    </small>
                                    <small class="text-muted">
                                        {{ image.upload_time.strftime('%Y-%m-%d') if image.upload_time else '未知' }}
                                    </small>
                                </div>
                            </div>
                            <div class="card-footer">
                                <div class="d-flex justify-content-between">
                                    <span>
                                        <i class="bi bi-eye"></i> {{ image.views }}
                                        <i class="bi bi-heart ms-2"></i> {{ image.likes }}
                                    </span>
                                    <a href="/image/{{ image.id }}" class="btn btn-sm btn-outline-primary">
                                        查看详情
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                
                <!-- 分页 -->
                {% if search_result.pages > 1 %}
                <nav aria-label="搜索结果分页" class="mt-4">
                    <ul class="pagination justify-content-center">
                        {% if search_result.page > 1 %}
                        <li class="page-item">
                            <a class="page-link" href="?q={{ query }}&page={{ search_result.page - 1 }}">
                                上一页
                            </a>
                        </li>
                        {% else %}
                        <li class="page-item disabled">
                            <span class="page-link">上一页</span>
                        </li>
                        {% endif %}
                        
                        {% for page_num in range(1, search_result.pages + 1) %}
                            {% if page_num == search_result.page %}
                            <li class="page-item active">
                                <span class="page-link">{{ page_num }}</span>
                            </li>
                            {% elif page_num >= search_result.page - 2 and page_num <= search_result.page + 2 %}
                            <li class="page-item">
                                <a class="page-link" href="?q={{ query }}&page={{ page_num }}">{{ page_num }}</a>
                            </li>
                            {% elif page_num == 1 %}
                            <li class="page-item">
                                <a class="page-link" href="?q={{ query }}&page=1">1</a>
                            </li>
                            {% elif page_num == search_result.pages %}
                            <li class="page-item">
                                <a class="page-link" href="?q={{ query }}&page={{ search_result.pages }}">{{ search_result.pages }}</a>
                            </li>
                            {% endif %}
                        {% endfor %}
                        
                        {% if search_result.page < search_result.pages %}
                        <li class="page-item">
                            <a class="page-link" href="?q={{ query }}&page={{ search_result.page + 1 }}">
                                下一页
                            </a>
                        </li>
                        {% else %}
                        <li class="page-item disabled">
                            <span class="page-link">下一页</span>
                        </li>
                        {% endif %}
                    </ul>
                </nav>
                {% endif %}
                
            {% else %}
                <div class="alert alert-info text-center py-5">
                    <i class="bi bi-search display-4 text-muted mb-3"></i>
                    <h4>没有找到相关图片</h4>
                    <p class="mb-0">尝试使用其他关键词搜索</p>
                </div>
            {% endif %}
        {% else %}
            <div class="alert alert-light text-center py-5">
                <i class="bi bi-search display-4 text-muted mb-3"></i>
                <h4>请输入搜索关键词</h4>
                <p class="mb-0">在搜索框中输入关键词，查找您感兴趣的图片</p>
            </div>
        {% endif %}
        
        <div class="mt-4 text-center">
            <a href="/" class="btn btn-outline-secondary">
                <i class="bi bi-arrow-left"></i> 返回首页
            </a>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // 图片加载失败处理
        document.querySelectorAll('img').forEach(function(img) {
            img.onerror = function() {
                if (this.src.indexOf('uploads/') !== -1) {
                    this.src = 'https://via.placeholder.com/300x200/cccccc/969696?text=图片加载失败';
                }
            };
        });
    </script>
</body>
</html>'''
    
    # 写入文件
    with open(search_html_path, 'w', encoding='utf-8') as f:
        f.write(new_search_html)
    
    print("✅ 已修复search.html模板")
    return True

def create_test_script():
    """创建测试脚本"""
    test_script = '''import requests
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
    print("\\n2. 测试搜索功能...")
    
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
    
    print("\\n3. 测试数据库连接...")
    try:
        # 测试数据库连接状态
        response = requests.get(base_url, timeout=5)
        if "数据库" in response.text:
            print("   ✅ 数据库连接正常")
        else:
            print("   ⚠️  无法确认数据库状态")
    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
    
    print("\\n" + "=" * 50)
    print("测试完成！")
    print("\\n提示：")
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
'''
    
    with open("test_app.py", 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ 已创建测试脚本 test_app.py")
    return True

def main():
    print("开始修复搜索功能...")
    print("=" * 50)
    
    # 检查文件是否存在
    if not os.path.exists("app.py"):
        print("❌ 错误: app.py 文件不存在")
        return
    
    if not os.path.exists("templates"):
        os.makedirs("templates", exist_ok=True)
    
    # 修复文件
    fix_app_py()
    fix_search_html()
    create_test_script()
    
    print("=" * 50)
    print("✅ 修复完成！")
    print("\\n下一步操作:")
    print("1. 启动Flask应用: python app.py")
    print("2. 测试搜索功能: python test_app.py")
    print("3. 在浏览器中访问: http://localhost:5000")
    print("4. 测试搜索关键词: 'landscape', 'admin', 'test'")

if __name__ == "__main__":
    main()