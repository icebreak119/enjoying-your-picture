import mysql.connector

def test_db_connection()
    测试数据库连接
    config = {
        'host' 'localhost',
        'user' 'pic_share_user',
        'password' '123456',
        'database' 'pic_share_db',
        'charset' 'utf8mb4'
    }
    
    try
        # 测试应用使用的连接
        conn = mysql.connector.connect(config)
        cursor = conn.cursor(dictionary=True)
        
        print(✅ 1. 数据库连接成功！)
        
        # 检查用户表
        cursor.execute(SELECT COUNT() as count FROM users)
        users_count = cursor.fetchone()['count']
        print(f✅ 2. 用户表检查 {users_count} 个用户)
        
        # 检查图片表
        cursor.execute(SELECT COUNT() as count FROM images)
        images_count = cursor.fetchone()['count']
        print(f✅ 3. 图片表检查 {images_count} 张图片)
        
        # 检查点赞表
        cursor.execute(SELECT COUNT() as count FROM likes)
        likes_count = cursor.fetchone()['count']
        print(f✅ 4. 点赞表检查 {likes_count} 条点赞记录)
        
        # 显示测试用户
        cursor.execute(SELECT id, username, email FROM users)
        users = cursor.fetchall()
        print(n📋 测试用户列表)
        for user in users
            print(f  - {user['username']} ({user['email']}) - 密码 123456)
        
        cursor.close()
        conn.close()
        
        print(n🎉 数据库连接测试完成！)
        return True
        
    except Exception as e
        print(f❌ 连接失败 {e})
        return False

def test_app_connection()
    测试应用配置
    print(n🔍 检查app.py配置)
    
    # 检查数据库配置
    from app import DB_CONFIG
    print(f  主机 {DB_CONFIG['host']})
    print(f  用户 {DB_CONFIG['user']})
    print(f  数据库 {DB_CONFIG['database']})
    print(f  字符集 {DB_CONFIG['charset']})
    
    # 检查静态文件目录
    import os
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    uploads_dir = os.path.join(static_dir, 'uploads')
    
    print(fn📁 目录检查)
    print(f  静态文件目录 {'✅ 存在' if os.path.exists(static_dir) else '❌ 不存在'})
    print(f  上传目录 {'✅ 存在' if os.path.exists(uploads_dir) else '⚠️  不存在，但应用启动时会自动创建'})

if __name__ == __main__
    print(开始测试数据库连接...)
    print(=  50)
    
    test_app_connection()
    print(n + =  50)
    
    if test_db_connection()
        print(n✅ 所有测试通过！您可以启动应用了。)
        print(n启动命令 python app.py)
        print(访问地址 httplocalhost5000)
        print(n测试账号 admin  123456)
        print(测试账号 test  123456)
    else
        print(n❌ 测试失败，请检查配置。)