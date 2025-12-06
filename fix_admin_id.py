import mysql.connector
from mysql.connector import Error

def fix_admin_id():
    """修复管理员ID为1"""
    
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': '123456',
        'database': 'pic_share_db',
        'charset': 'utf8mb4'
    }
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        print("正在修复管理员ID...")
        
        # 1. 检查当前管理员ID
        cursor.execute("SELECT id, username FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()
        
        if admin_user:
            current_id = admin_user[0]
            print(f"当前admin用户ID: {current_id}")
            
            if current_id != 1:
                print(f"admin用户ID不为1，需要修复...")
                
                # 检查ID=1是否被占用
                cursor.execute("SELECT username FROM users WHERE id = 1")
                id_1_user = cursor.fetchone()
                
                if id_1_user:
                    # ID=1被其他用户占用
                    other_username = id_1_user[0]
                    print(f"ID=1被用户 '{other_username}' 占用")
                    
                    # 方案A：交换ID
                    max_id_query = "SELECT COALESCE(MAX(id), 0) + 1 FROM users"
                    cursor.execute(max_id_query)
                    new_id = cursor.fetchone()[0]
                    
                    # 更新其他用户ID
                    cursor.execute("UPDATE users SET id = %s WHERE id = 1", (new_id,))
                    
                    # 更新admin用户ID为1
                    cursor.execute("UPDATE users SET id = 1 WHERE username = 'admin'")
                    
                    print(f"已将用户 '{other_username}' 的ID改为 {new_id}")
                    print(f"已将admin用户ID改为 1")
                    
                else:
                    # ID=1空闲，直接更新
                    cursor.execute("UPDATE users SET id = 1 WHERE username = 'admin'")
                    print("已将admin用户ID改为 1")
                
                conn.commit()
            else:
                print("✅ admin用户ID已经是1，无需修复")
        else:
            print("❌ 未找到admin用户")
            
        # 2. 显示最终结果
        print("\n最终用户列表：")
        cursor.execute("SELECT id, username, email FROM users ORDER BY id")
        users = cursor.fetchall()
        
        for user in users:
            print(f"  ID={user[0]}: {user[1]} ({user[2]})")
        
        cursor.close()
        conn.close()
        
    except Error as e:
        print(f"❌ 修复失败: {e}")

def check_admin_permission():
    """检查代码中的管理员权限"""
    print("\n检查管理员权限设置...")
    
    # 检查app.py中的权限判断
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找权限检查代码
    if 'current_user.id != 1' in content:
        print("⚠️  发现使用ID=1判断管理员权限")
        print("   建议修改为使用用户名判断：current_user.username != 'admin'")
    elif "current_user.username != 'admin'" in content:
        print("✅ 使用用户名判断管理员权限")
    else:
        print("⚠️  未找到明确的管理员权限检查")
    
    # 显示相关代码片段
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'current_user.id != result' in line or 'current_user.id != 1' in line:
            print(f"\n行 {i+1}: {line.strip()}")

if __name__ == "__main__":
    print("管理员ID修复工具")
    print("=" * 50)
    
    # 修复ID
    fix_admin_id()
    
    # 检查权限设置
    check_admin_permission()
    
    print("\n" + "=" * 50)
    print("完成！")
    print("\n登录信息：")
    print("用户名: admin")
    print("密码: 123456")