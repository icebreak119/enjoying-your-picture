"""
图片分享网站 - 适配pic_share_db数据库结构
修复Flask-Login的is_active属性问题
修复搜索功能问题
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error
import uuid
from PIL import Image
import math

# ====================== 1. 初始化Flask应用 ======================
app = Flask(__name__, static_folder='static', static_url_path='/static')

# ====================== 2. MySQL数据库配置 ======================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'pic_share_user',
    'password': '123456',
    'database': 'pic_share_db',
    'charset': 'utf8mb4'
}

# ====================== 3. 基础配置 ======================
app.config['SECRET_KEY'] = 'dev-pic-share-2025-123456'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

# ====================== 4. 日志配置 ======================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ====================== 5. 初始化Flask-Login ======================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录以访问该页面！'
login_manager.login_message_category = 'warning'

# ====================== 6. 数据库辅助函数 ======================
def get_db_connection():
    """获取数据库连接"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        logger.error(f"数据库连接失败: {e}")
        try:
            backup_config = DB_CONFIG.copy()
            backup_config['user'] = 'root'
            backup_config['password'] = '123456'
            conn = mysql.connector.connect(**backup_config)
            logger.info("使用root用户连接数据库成功")
            return conn
        except Error as e2:
            logger.error(f"备用连接也失败: {e2}")
        return None

def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """执行SQL查询"""
    conn = get_db_connection()
    if conn is None:
        return None

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())

        if commit:
            conn.commit()

        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        elif commit:
            result = cursor.lastrowid
        else:
            result = None

        return result
    except Error as e:
        logger.error(f"SQL执行失败: {e}")
        logger.error(f"SQL查询: {query}")
        logger.error(f"参数: {params}")
        if conn:
            conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ====================== 7. 数据模型 ======================
class User(UserMixin):
    def __init__(self, id, username, email, password_hash, created_at=None, is_active=True):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at
        self._is_active = is_active

    @property
    def is_active(self):
        return self._is_active

    @property
    def is_admin(self):
        """判断是否为管理员"""
        # 用户名为admin或ID为1的用户视为管理员
        return self.username == 'admin' or self.id == 1

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    @staticmethod
    def get_by_id(user_id):
        query = "SELECT * FROM users WHERE id = %s"
        result = execute_query(query, (user_id,), fetch_one=True)
        if result:
            return User(
                id=result['id'],
                username=result['username'],
                email=result['email'],
                password_hash=result['password_hash'],
                created_at=result.get('created_at'),
                is_active=bool(result.get('is_active', True))
            )
        return None

    @staticmethod
    def get_by_username(username):
        query = "SELECT * FROM users WHERE username = %s"
        result = execute_query(query, (username,), fetch_one=True)
        if result:
            return User(
                id=result['id'],
                username=result['username'],
                email=result['email'],
                password_hash=result['password_hash'],
                created_at=result.get('created_at'),
                is_active=bool(result.get('is_active', True))
            )
        return None

    @staticmethod
    def get_by_email(email):
        query = "SELECT * FROM users WHERE email = %s"
        result = execute_query(query, (email,), fetch_one=True)
        if result:
            return User(
                id=result['id'],
                username=result['username'],
                email=result['email'],
                password_hash=result['password_hash'],
                created_at=result.get('created_at'),
                is_active=bool(result.get('is_active', True))
            )
        return None

    @staticmethod
    def create(username, password, email=None):
        password_hash = generate_password_hash(password)
        query = """
            INSERT INTO users (username, email, password_hash, is_active)
            VALUES (%s, %s, %s, %s)
        """
        user_id = execute_query(query, (username, email, password_hash, True), commit=True)
        if user_id:
            return User.get_by_id(user_id)
        return None

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ====================== 8. Flask-Login用户加载器 ======================
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.get_by_id(int(user_id))
    except:
        return None

# ====================== 9. 辅助函数 ======================
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def ensure_upload_folder():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        logger.info(f"创建上传文件夹：{app.config['UPLOAD_FOLDER']}")

def create_thumbnail(image_path, max_size=(300, 200)):
    """创建缩略图"""
    try:
        with Image.open(image_path) as img:
            img.thumbnail(max_size)
            thumbnail_name = f"thumb_{os.path.basename(image_path)}"
            thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_name)
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background

            if thumbnail_name.lower().endswith('.jpg') or thumbnail_name.lower().endswith('.jpeg'):
                img.save(thumbnail_path, 'JPEG', quality=85)
            else:
                img.save(thumbnail_path, 'PNG')
            return thumbnail_name
    except Exception as e:
        logger.error(f"创建缩略图失败: {e}")
        return None

# ====================== 10. 上下文处理器 ======================
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# ====================== 11. 核心路由 ======================
@app.route('/')
def index():
    """首页 - 展示所有公开图片"""
    try:
        query = """
            SELECT i.*, u.username 
            FROM images i 
            LEFT JOIN users u ON i.user_id = u.id 
            WHERE i.is_active = TRUE OR i.is_active IS NULL
            ORDER BY i.upload_time DESC
            LIMIT 30
        """
        results = execute_query(query, fetch_all=True)

        images = []
        if results:
            for row in results:
                file_path = row['file_path']
                if file_path.startswith('/'):
                    file_path = file_path[1:]

                image = {
                    'id': row['id'],
                    'filename': row['filename'],
                    'original_filename': row['original_name'],
                    'title': row['title'] or row['original_name'],
                    'description': row['description'] or '',
                    'user_id': row['user_id'],
                    'upload_time': row['upload_time'],
                    'views': row.get('views', 0),
                    'likes': row.get('likes', 0),
                    'username': row['username'],
                    'file_path': file_path,
                    'author': {'username': row['username']}
                }
                images.append(image)
    except Exception as e:
        logger.error(f"获取图片失败: {e}")
        images = []

    return render_template('index.html', images=images)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('用户名和密码不能为空！', 'danger')
            return render_template('login.html')

        user = User.get_by_username(username)

        if user is None:
            flash('用户名不存在！', 'danger')
        elif not user.check_password(password):
            flash('密码错误！', 'danger')
        elif not user.is_active:
            flash('账号已被禁用！', 'danger')
        else:
            login_user(user, remember=True)
            flash(f'欢迎回来，{username}！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not password or not email:
            flash('用户名、邮箱和密码不能为空！', 'danger')
        elif len(username) < 3:
            flash('用户名至少3个字符！', 'danger')
        elif len(password) < 6:
            flash('密码至少6个字符！', 'danger')
        elif password != confirm_password:
            flash('两次密码不一致！', 'danger')
        elif User.get_by_username(username):
            flash('用户名已存在！', 'danger')
        else:
            existing_email = User.get_by_email(email)
            if existing_email:
                flash('邮箱已被注册！', 'danger')
            else:
                user = User.create(username, password, email)
                if user:
                    flash('注册成功！请登录', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('注册失败，请稍后重试', 'danger')

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    flash(f'再见，{username}！已成功退出', 'info')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """图片上传功能"""
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('未选择文件！', 'danger')
            return redirect(request.url)

        file = request.files['image']

        if file.filename == '':
            flash('未选择文件！', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            ext = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{ext}"

            ensure_upload_folder()

            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(filepath)

            thumbnail_name = create_thumbnail(filepath)

            file_size = os.path.getsize(filepath)
            mime_type = file.content_type or f"image/{ext}"

            title = request.form.get('title', '').strip()
            if not title:
                title = original_filename.rsplit('.', 1)[0]

            description = request.form.get('description', '').strip()

            insert_query = """
                INSERT INTO images 
                (filename, original_name, file_path, file_size, mime_type, 
                 title, description, user_id, upload_time, views, likes, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            params = (
                unique_filename,
                original_filename,
                f"uploads/{unique_filename}",
                file_size,
                mime_type,
                title,
                description,
                current_user.id,
                datetime.now(),
                0,
                0,
                True
            )

            result = execute_query(insert_query, params, commit=True)

            if result:
                if thumbnail_name:
                    update_query = "UPDATE images SET thumbnail_path = %s WHERE id = %s"
                    execute_query(update_query, (f"uploads/{thumbnail_name}", result), commit=True)

                flash('图片上传成功！', 'success')
                return redirect(url_for('index'))
            else:
                flash('图片保存失败，数据库错误', 'danger')
        else:
            flash('不支持的文件格式！仅支持PNG/JPG/JPEG/GIF/WEBP', 'danger')

    return render_template('upload.html')

@app.route('/image/<int:image_id>')
def image_detail(image_id):
    """图片详情页"""
    query = """
        SELECT i.*, u.username 
        FROM images i 
        LEFT JOIN users u ON i.user_id = u.id 
        WHERE i.id = %s
    """
    result = execute_query(query, (image_id,), fetch_one=True)

    if not result:
        flash('图片不存在！', 'danger')
        return redirect(url_for('index'))

    update_query = "UPDATE images SET views = views + 1 WHERE id = %s"
    execute_query(update_query, (image_id,), commit=True)

    file_path = result['file_path']
    if file_path.startswith('/'):
        file_path = file_path[1:]

    thumbnail_path = result.get('thumbnail_path')
    if thumbnail_path and thumbnail_path.startswith('/'):
        thumbnail_path = thumbnail_path[1:]

    image = {
        'id': result['id'],
        'filename': result['filename'],
        'original_filename': result['original_name'],
        'title': result['title'] or result['original_name'],
        'description': result['description'] or '',
        'user_id': result['user_id'],
        'upload_time': result.get('upload_time', datetime.now()),
        'views': result.get('views', 0) + 1,
        'likes': result.get('likes', 0),
        'username': result['username'],
        'file_path': file_path,
        'thumbnail_path': thumbnail_path,
        'file_size': result.get('file_size', 0),
        'mime_type': result.get('mime_type', 'image/jpeg'),
        'author': {'username': result['username']}
    }

    return render_template('image_detail.html', image=image)

@app.route('/like/<int:image_id>')
@login_required
def like_image(image_id):
    """图片点赞"""
    check_query = "SELECT * FROM images WHERE id = %s"
    image = execute_query(check_query, (image_id,), fetch_one=True)

    if not image:
        flash('图片不存在！', 'danger')
        return redirect(url_for('index'))

    check_like_query = """
        SELECT id FROM likes WHERE user_id = %s AND image_id = %s
    """
    existing_like = execute_query(check_like_query, (current_user.id, image_id), fetch_one=True)

    if existing_like:
        delete_like_query = "DELETE FROM likes WHERE user_id = %s AND image_id = %s"
        execute_query(delete_like_query, (current_user.id, image_id), commit=True)

        update_query = "UPDATE images SET likes = GREATEST(0, likes - 1) WHERE id = %s"
        execute_query(update_query, (image_id,), commit=True)
        flash('已取消点赞！', 'info')
    else:
        like_query = "INSERT INTO likes (user_id, image_id) VALUES (%s, %s)"
        execute_query(like_query, (current_user.id, image_id), commit=True)

        update_query = "UPDATE images SET likes = likes + 1 WHERE id = %s"
        execute_query(update_query, (image_id,), commit=True)
        flash('点赞成功！', 'success')

    return redirect(request.referrer or url_for('index'))

@app.route('/delete/<int:image_id>', methods=['POST'])
@login_required
def delete_image(image_id):
    """删除图片 - 管理员可以删除任何图片"""
    query = "SELECT * FROM images WHERE id = %s"
    result = execute_query(query, (image_id,), fetch_one=True)

    if not result:
        flash('图片不存在！', 'danger')
        return redirect(url_for('index'))

    # 权限检查：管理员可以删除任何图片，非管理员只能删除自己的图片
    if current_user.id != result['user_id'] and not current_user.is_admin:
        flash('无权限删除该图片！', 'danger')
        return redirect(url_for('image_detail', image_id=image_id))

    try:
        filename = result['filename']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)

        if result.get('thumbnail_path'):
            thumb_filename = result['thumbnail_path'].split('/')[-1]
            thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], thumb_filename)
            if os.path.exists(thumb_path):
                os.remove(thumb_path)

        delete_query = "DELETE FROM images WHERE id = %s"
        execute_query(delete_query, (image_id,), commit=True)

        delete_likes_query = "DELETE FROM likes WHERE image_id = %s"
        execute_query(delete_likes_query, (image_id,), commit=True)

        flash('图片删除成功！', 'success')
    except Exception as e:
        logger.error(f"删除图片失败：{e}")
        flash(f'删除失败：{str(e)}', 'danger')

    return redirect(url_for('index'))

@app.route('/my-images')
@login_required
def my_images():
    """查看我的图片"""
    query = """
        SELECT * FROM images 
        WHERE user_id = %s
        ORDER BY upload_time DESC
    """
    results = execute_query(query, (current_user.id,), fetch_all=True)

    images = []
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
                'file_path': file_path,
                'thumbnail_path': thumbnail_path
            }
            images.append(image)

    return render_template('my_images.html', images=images)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """提供上传图片的访问"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ====================== 12. 搜索功能（终极修复版） ======================
@app.route('/search')
def search():
    """搜索功能 - 多字段搜索（标题、描述、用户名）和分页"""
    try:
        query_text = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = 12

        logger.info(f"搜索请求: query='{query_text}', page={page}")

        # 准备空的搜索结果结构 - 使用非常独特的变量名
        search_result_data = {
            'items_list': [],
            'current_page': page,
            'total_pages': 1,
            'total_count': 0,
            'per_page': per_page
        }

        # 如果搜索关键词为空
        if not query_text:
            logger.info("空搜索请求")
            return render_template('search.html',
                                   search_query=query_text,
                                   result_data=search_result_data)

        # 执行搜索
        search_param = f"%{query_text}%"
        offset = (page - 1) * per_page

        # 搜索查询SQL
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

        # 处理搜索结果
        images_list = []
        if results:
            for row in results:
                # 处理文件路径
                file_path = row['file_path']
                if file_path.startswith('/'):
                    file_path = file_path[1:]

                thumbnail_path = row.get('thumbnail_path')
                if thumbnail_path and thumbnail_path.startswith('/'):
                    thumbnail_path = thumbnail_path[1:]

                # 构建图片对象
                image_obj = {
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
                images_list.append(image_obj)

        # 获取总数
        count_query = """
            SELECT COUNT(*) as total_count 
            FROM images i 
            LEFT JOIN users u ON i.user_id = u.id 
            WHERE (i.title LIKE %s OR i.description LIKE %s OR u.username LIKE %s)
        """
        count_result = execute_query(count_query, (search_param, search_param, search_param), fetch_one=True)

        total = count_result['total_count'] if count_result else 0

        # 计算总页数
        pages = math.ceil(total / per_page) if total > 0 else 1

        # 更新搜索数据
        search_result_data.update({
            'items_list': images_list,
            'current_page': page,
            'total_pages': pages,
            'total_count': total
        })

        logger.info(f"搜索成功: 关键词='{query_text}', 结果数={total}, 当前页={page}, 总页数={pages}")
        return render_template('search_simple.html',
                               search_query=query_text,
                               result_data=search_result_data)

    except Exception as e:
        logger.error(f"搜索失败: {e}", exc_info=True)
        flash('搜索时发生错误，请稍后重试', 'danger')

        # 返回错误时的空结果
        error_data = {
            'items_list': [],
            'current_page': 1,
            'total_pages': 1,
            'total_count': 0,
            'per_page': 12
        }
        return render_template('search.html',
                               search_query=query_text,
                               result_data=error_data)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('index.html', error_404=True), 404

@app.errorhandler(500)
def internal_server_error(error):
    logger.error(f"服务器内部错误：{error}")
    return render_template('index.html', error_500=True), 500

@app.errorhandler(413)
def request_too_large(error):
    return render_template('index.html', error_413=True), 413

# ====================== 14. 初始化函数 ======================
def init_app():
    """初始化应用"""
    ensure_upload_folder()

    try:
        # 检查并创建likes表
        check_likes_query = "SHOW TABLES LIKE 'likes'"
        likes_table = execute_query(check_likes_query, fetch_one=True)

        if not likes_table:
            create_likes_query = """
                CREATE TABLE IF NOT EXISTS likes (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    user_id INT NOT NULL,
                    image_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
                    UNIQUE KEY unique_like (user_id, image_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
            execute_query(create_likes_query, commit=True)
            logger.info("创建likes表成功")

        # 检查images表是否有likes字段
        check_likes_column = "SHOW COLUMNS FROM images LIKE 'likes'"
        has_likes_column = execute_query(check_likes_column, fetch_one=True)

        if not has_likes_column:
            alter_query = "ALTER TABLE images ADD COLUMN likes INT DEFAULT 0"
            execute_query(alter_query, commit=True)
            logger.info("为images表添加likes字段成功")

        # 检查images表是否有is_active字段
        check_is_active_column = "SHOW COLUMNS FROM images LIKE 'is_active'"
        has_is_active_column = execute_query(check_is_active_column, fetch_one=True)

        if not has_is_active_column:
            alter_query = "ALTER TABLE images ADD COLUMN is_active BOOLEAN DEFAULT TRUE"
            execute_query(alter_query, commit=True)
            logger.info("为images表添加is_active字段成功")

        # 检查images表是否有thumbnail_path字段
        check_thumbnail_column = "SHOW COLUMNS FROM images LIKE 'thumbnail_path'"
        has_thumbnail_column = execute_query(check_thumbnail_column, fetch_one=True)

        if not has_thumbnail_column:
            alter_query = "ALTER TABLE images ADD COLUMN thumbnail_path VARCHAR(500)"
            execute_query(alter_query, commit=True)
            logger.info("为images表添加thumbnail_path字段成功")

        logger.info("数据库初始化完成")

    except Exception as e:
        logger.error(f"数据库检查失败: {e}")

# ====================== 15. 启动应用 ======================
if __name__ == '__main__':
    init_app()

    port = int(os.environ.get('PORT', 5000))
    logger.info(f"启动应用：http://localhost:{port}")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        threaded=True
    )