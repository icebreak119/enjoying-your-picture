"""
我的图片分享网站 - 主程序文件
已修复Railway部署问题
"""

from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# 创建Flask应用 - 关键修改：指定静态文件路径
app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-this-in-production')
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # 上传文件保存的文件夹
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传大小为16MB
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}  # 允许的文件类型

# 处理上传文件的访问
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """提供上传的图片文件"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except:
        # 如果文件不存在，返回默认图片
        return redirect('https://via.placeholder.com/300x200/cccccc/969696?text=图片未找到')

# 健康检查路由
@app.route('/health')
def health_check():
    """健康检查路由，用于Railway监控"""
    return 'OK', 200

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 设置登录页面的路由
login_manager.login_message = '请先登录以访问此页面。'
login_manager.login_message_category = 'warning'

# 用户类（简化的内存存储版本）
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.created_at = datetime.now()

# 图片类
class Image:
    def __init__(self, id, filename, title, description, user_id):
        self.id = id
        self.filename = filename
        self.title = title
        self.description = description
        self.user_id = user_id
        self.likes = 0
        self.created_at = datetime.now()

# 模拟数据库（实际项目要用真实数据库）
# 用户数据
users = {
    1: User(1, 'admin', generate_password_hash('admin123')),
    2: User(2, 'test', generate_password_hash('test123'))
}

# 图片数据
images = [
    Image(1, 'example1.jpg', '美丽的风景', '这是一张美丽的风景图片，拍摄于山间。', 1),
    Image(2, 'example2.jpg', '可爱的小猫', '一只可爱的小猫在玩耍。', 2)
]

# 为示例图片添加一些点赞
images[0].likes = 5
images[1].likes = 3

# 添加上下文处理器
@app.context_processor
def inject_now():
    """注入当前时间到所有模板"""
    return {'now': datetime.now()}

@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    return users.get(int(user_id))

def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """首页 - 显示所有图片"""
    # 按创建时间倒序排列（最新的在前面）
    sorted_images = sorted(images, key=lambda x: x.created_at, reverse=True)
    return render_template('index.html', images=sorted_images)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    # 如果用户已经登录，重定向到首页
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        # 查找用户
        user = None
        for u in users.values():
            if u.username == username and check_password_hash(u.password_hash, password):
                user = u
                break

        if user:
            login_user(user, remember=True)
            flash(f'欢迎回来，{username}！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('用户名或密码错误，请重试。', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    # 如果用户已经登录，重定向到首页
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # 验证输入
        if not username or not password:
            flash('用户名和密码不能为空。', 'danger')
        elif len(username) < 3:
            flash('用户名至少需要3个字符。', 'danger')
        elif len(password) < 6:
            flash('密码至少需要6个字符。', 'danger')
        elif password != confirm_password:
            flash('两次输入的密码不一致。', 'danger')
        else:
            # 检查用户名是否已存在
            for u in users.values():
                if u.username == username:
                    flash('用户名已存在，请选择其他用户名。', 'danger')
                    return render_template('register.html')

            # 创建新用户
            new_id = max(users.keys()) + 1 if users else 1
            new_user = User(new_id, username, generate_password_hash(password))
            users[new_id] = new_user

            flash('注册成功！请登录。', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """退出登录"""
    username = current_user.username
    logout_user()
    flash(f'再见，{username}！您已成功退出。', 'info')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """上传图片页面"""
    if request.method == 'POST':
        # 检查是否有文件被上传
        if 'file' not in request.files:
            flash('没有选择文件。', 'danger')
            return redirect(request.url)

        file = request.files['file']

        # 如果用户没有选择文件
        if file.filename == '':
            flash('没有选择文件。', 'danger')
            return redirect(request.url)

        # 检查文件类型
        if file and allowed_file(file.filename):
            # 安全地获取文件名
            filename = secure_filename(file.filename)

            # 确保上传文件夹存在
            upload_folder = app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder, exist_ok=True)

            # 保存文件
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)

            # 获取表单数据
            title = request.form.get('title', '无标题').strip()
            description = request.form.get('description', '').strip()

            # 创建图片对象
            new_id = max([img.id for img in images]) + 1 if images else 1
            new_image = Image(
                id=new_id,
                filename=filename,
                title=title if title else '无标题',
                description=description,
                user_id=current_user.id
            )

            # 添加到图片列表
            images.append(new_image)

            flash('图片上传成功！', 'success')
            return redirect(url_for('index'))
        else:
            flash('不支持的文件类型。请上传 PNG、JPG、JPEG、GIF 或 WebP 格式的图片。', 'danger')

    return render_template('upload.html')

@app.route('/image/<int:image_id>')
def image_detail(image_id):
    """图片详情页面"""
    # 查找图片
    image = None
    for img in images:
        if img.id == image_id:
            image = img
            break

    if image is None:
        flash('图片不存在。', 'danger')
        return redirect(url_for('index'))

    # 查找上传者用户名
    uploader = users.get(image.user_id)
    uploader_name = uploader.username if uploader else '未知用户'

    return render_template('image_detail.html', image=image, uploader_name=uploader_name)

@app.route('/like/<int:image_id>')
@login_required
def like_image(image_id):
    """给图片点赞"""
    # 查找图片
    image = None
    for img in images:
        if img.id == image_id:
            image = img
            break

    if image is None:
        flash('图片不存在。', 'danger')
        return redirect(url_for('index'))

    # 增加点赞数
    image.likes += 1
    flash('点赞成功！', 'success')

    # 返回来源页面或首页
    referrer = request.referrer
    return redirect(referrer) if referrer else redirect(url_for('index'))

@app.route('/delete/<int:image_id>')
@login_required
def delete_image(image_id):
    """删除图片（仅上传者或管理员可以删除）"""
    # 查找图片
    image = None
    for img in images:
        if img.id == image_id:
            image = img
            break

    if image is None:
        flash('图片不存在。', 'danger')
        return redirect(url_for('index'))

    # 检查权限：上传者或管理员（id=1）
    if current_user.id != image.user_id and current_user.id != 1:
        flash('您没有权限删除此图片。', 'danger')
        return redirect(url_for('image_detail', image_id=image_id))

    try:
        # 删除文件
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        if os.path.exists(filepath):
            os.remove(filepath)

        # 从列表中删除
        images.remove(image)
        flash('图片删除成功。', 'success')
    except Exception as e:
        flash(f'删除图片时出错：{str(e)}', 'danger')

    return redirect(url_for('index'))

@app.route('/about')
def about():
    """关于页面"""
    return render_template('index.html', about_page=True)

@app.errorhandler(404)
def page_not_found(error):
    """404错误页面"""
    return render_template('index.html', error_404=True), 404

@app.errorhandler(500)
def internal_server_error(error):
    """500错误页面"""
    return render_template('index.html', error_500=True), 500

if __name__ == '__main__':
    # 确保上传文件夹存在
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)

    # 获取环境变量中的端口，如果没有则使用5000
    port = int(os.environ.get('PORT', 5000))

    # 生产环境设置
    debug_mode = os.environ.get('FLASK_ENV') != 'production'

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode
    )