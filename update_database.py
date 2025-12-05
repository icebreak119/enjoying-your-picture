"""
更新数据库表结构（使用密码123456）
"""
import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # 改为root用户
    'password': '123456',
    'database': 'image_sharing_db'
}

def update_database():
    conn = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        print("检查并更新数据库表结构...")
        
        # 1. 检查images表的字段
        cursor.execute("SHOW COLUMNS FROM images")
        columns = [col['Field'] for col in cursor.fetchall()]
        print(f"当前images表的字段: {columns}")
        
        # 添加缺失的字段
        if 'is_public' not in columns:
            print("添加is_public字段...")
            cursor.execute("ALTER TABLE images ADD COLUMN is_public BOOLEAN DEFAULT TRUE")
            
        if 'likes' not in columns:
            print("添加likes字段...")
            cursor.execute("ALTER TABLE images ADD COLUMN likes INT DEFAULT 0")
            
        if 'views' not in columns:
            print("添加views字段...")
            cursor.execute("ALTER TABLE images ADD COLUMN views INT DEFAULT 0")
            
        # 2. 检查users表
        cursor.execute("SHOW COLUMNS FROM users")
        columns = [col['Field'] for col in cursor.fetchall()]
        print(f"当前users表的字段: {columns}")
        
        if 'email' not in columns:
            print("添加email字段...")
            cursor.execute("ALTER TABLE users ADD COLUMN email VARCHAR(100)")
            
        # 3. 检查是否有is_active字段（在images表中）
        cursor.execute("SHOW COLUMNS FROM images LIKE 'is_active'")
        result = cursor.fetchone()
        if not result:
            print("添加is_active字段到images表...")
            cursor.execute("ALTER TABLE images ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            
        conn.commit()
        print("✅ 数据库更新完成！")
        
    except Exception as e:
        print(f"❌ 数据库更新失败: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    update_database()