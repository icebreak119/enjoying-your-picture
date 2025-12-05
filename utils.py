import os
import uuid
from PIL import Image as PILImage
from werkzeug.utils import secure_filename
from flask import current_app
from models import db, Tag, ImageTag
import re


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def generate_unique_filename(original_filename):
    """生成唯一的文件名"""
    ext = original_filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    return unique_filename


def save_uploaded_file(file, user_id):
    """保存上传的文件并生成缩略图"""
    if not allowed_file(file.filename):
        return None, None

    # 创建用户目录
    user_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    # 生成文件名
    original_filename = secure_filename(file.filename)
    unique_filename = generate_unique_filename(original_filename)

    # 保存原始图片
    file_path = os.path.join(user_dir, unique_filename)
    file.save(file_path)

    # 生成缩略图
    thumbnail_filename = f"thumb_{unique_filename}"
    thumbnail_path = os.path.join(user_dir, thumbnail_filename)
    create_thumbnail(file_path, thumbnail_path, max_size=(300, 300))

    return file_path, thumbnail_path


def create_thumbnail(source_path, thumbnail_path, max_size=(300, 300)):
    """创建缩略图"""
    try:
        img = PILImage.open(source_path)

        # 保持宽高比调整大小
        img.thumbnail(max_size, PILImage.Resampling.LANCZOS)

        # 如果是PNG保留透明度
        if img.mode in ('RGBA', 'LA'):
            background = PILImage.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        img.save(thumbnail_path, 'JPEG' if thumbnail_path.lower().endswith(('.jpg', '.jpeg')) else 'PNG')
        return True
    except Exception as e:
        print(f"创建缩略图失败: {e}")
        return False


def process_tags(tag_string, image):
    """处理标签字符串，创建或关联标签"""
    if not tag_string:
        return

    tags = [tag.strip() for tag in tag_string.split(',') if tag.strip()]

    for tag_name in tags:
        # 创建slug
        slug = re.sub(r'[^\w\s-]', '', tag_name.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')

        # 查找或创建标签
        tag = Tag.query.filter_by(slug=slug).first()
        if not tag:
            tag = Tag(name=tag_name, slug=slug)
            db.session.add(tag)
            db.session.flush()

        # 关联图片和标签
        if not any(t.id == tag.id for t in image.tags):
            image_tag = ImageTag(image_id=image.id, tag_id=tag.id)
            db.session.add(image_tag)

    db.session.commit()


def delete_image_files(image):
    """删除图片文件"""
    try:
        if os.path.exists(image.file_path):
            os.remove(image.file_path)
        if image.thumbnail_path and os.path.exists(image.thumbnail_path):
            os.remove(image.thumbnail_path)
        return True
    except Exception as e:
        print(f"删除文件失败: {e}")
        return False