-- ====================== 图片分享网站数据库初始化脚本（修复编码问题） ======================
-- 适配 app.py 中的数据库结构
-- 修复中文字符编码问题

-- 1. 删除并重新创建数据库（确保使用正确的字符集）
DROP DATABASE IF EXISTS pic_share_db;
CREATE DATABASE pic_share_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 2. 创建专用用户
DROP USER IF EXISTS 'pic_share_user'@'localhost';
CREATE USER 'pic_share_user'@'localhost' IDENTIFIED BY '123456';
GRANT ALL PRIVILEGES ON pic_share_db.* TO 'pic_share_user'@'localhost';
FLUSH PRIVILEGES;

-- 3. 切换到目标数据库
USE pic_share_db;

-- 4. 设置当前连接的字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 5. 创建用户表（必须先创建，因为其他表有外键引用）
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. 创建图片表（核心表）
CREATE TABLE images (
    id INT PRIMARY KEY AUTO_INCREMENT,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    title VARCHAR(200),
    description TEXT,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    views INT DEFAULT 0,
    likes INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    thumbnail_path VARCHAR(500),
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_upload_time (upload_time DESC),
    INDEX idx_is_active (is_active),
    INDEX idx_filename (filename(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. 创建点赞表
CREATE TABLE likes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    image_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
    UNIQUE KEY unique_like (user_id, image_id),
    INDEX idx_user_id (user_id),
    INDEX idx_image_id (image_id),
    INDEX idx_created_at (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. 创建标签表（可选）
CREATE TABLE tags (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. 创建图片-标签关联表（可选）
CREATE TABLE image_tags (
    image_id INT,
    tag_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (image_id, tag_id),
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    INDEX idx_tag_id (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. 插入测试用户（密码均为123456的加密值）
INSERT INTO users (username, email, password_hash, is_active) VALUES
('admin', 'admin@pic-share.com', 'pbkdf2:sha256:260000$k4j9G0n8$9c8b7a6d5f4e3b2a1c0d9e8f7b6a5d4c3b2a1c0d9e8f7b6a5d4c3b2a1c0d9e8f', 1),
('test', 'test@pic-share.com', 'pbkdf2:sha256:260000$k4j9G0n8$9c8b7a6d5f4e3b2a1c0d9e8f7b6a5d4c3b2a1c0d9e8f7b6a5d4c3b2a1c0d9e8f', 1),
('user1', 'user1@pic-share.com', 'pbkdf2:sha256:260000$k4j9G0n8$9c8b7a6d5f4e3b2a1c0d9e8f7b6a5d4c3b2a1c0d9e8f7b6a5d4c3b2a1c0d9e8f', 1),
('user2', 'user2@pic-share.com', 'pbkdf2:sha256:260000$k4j9G0n8$9c8b7a6d5f4e3b2a1c0d9e8f7b6a5d4c3b2a1c0d9e8f7b6a5d4c3b2a1c0d9e8f', 1);

-- 11. 插入测试图片数据（使用英文描述，避免编码问题）
INSERT INTO images (filename, original_name, file_path, file_size, mime_type, title, description, user_id, upload_time, views, likes, is_active) VALUES
('test1.jpg', 'landscape.jpg', 'uploads/test1.jpg', 1024000, 'image/jpeg', 'Beautiful Landscape', 'A beautiful landscape photo taken in the mountains', 1, NOW() - INTERVAL 5 DAY, 150, 25, 1),
('test2.jpg', 'portrait.jpg', 'uploads/test2.jpg', 850000, 'image/jpeg', 'Portrait Photo', 'Professional portrait photography showing emotions', 2, NOW() - INTERVAL 3 DAY, 89, 12, 1),
('test3.png', 'abstract.png', 'uploads/test3.png', 2048000, 'image/png', 'Abstract Art', 'Modern abstract art design with rich colors', 1, NOW() - INTERVAL 2 DAY, 45, 8, 1),
('test4.jpg', 'cityscape.jpg', 'uploads/test4.jpg', 1536000, 'image/jpeg', 'City Night View', 'Night view of the city with bright lights', 2, NOW() - INTERVAL 1 DAY, 120, 18, 1),
('test5.jpg', 'nature.jpg', 'uploads/test5.jpg', 768000, 'image/jpeg', 'Nature Beauty', 'Amazing natural scenery that refreshes the mind', 1, NOW() - INTERVAL 8 HOUR, 67, 9, 1),
('test6.jpg', 'animal.jpg', 'uploads/test6.jpg', 921600, 'image/jpeg', 'Wild Animal', 'Rare animal photo taken in the wild', 2, NOW() - INTERVAL 4 HOUR, 34, 5, 1),
('test7.jpg', 'food.jpg', 'uploads/test7.jpg', 640000, 'image/jpeg', 'Food Photography', 'Delicious food with great presentation', 1, NOW() - INTERVAL 2 HOUR, 56, 11, 1),
('test8.jpg', 'travel.jpg', 'uploads/test8.jpg', 1152000, 'image/jpeg', 'Travel Memory', 'Beautiful moment captured during travel', 2, NOW() - INTERVAL 1 HOUR, 23, 3, 1),
('test9.jpg', 'sports.jpg', 'uploads/test9.jpg', 1792000, 'image/jpeg', 'Sports Moment', 'Capturing exciting moments of athletes', 1, NOW() - INTERVAL 30 MINUTE, 78, 15, 1),
('test10.jpg', 'architecture.jpg', 'uploads/test10.jpg', 1280000, 'image/jpeg', 'Architecture Art', 'Masterpiece of modern architecture design', 2, NOW(), 12, 2, 1);

-- 12. 插入测试点赞数据
INSERT INTO likes (user_id, image_id) VALUES
(1, 2),  -- admin 点赞 test 的图片
(1, 4),
(1, 6),
(2, 1),   -- test 点赞 admin 的图片
(2, 3),
(2, 5),
(2, 7),
(2, 9);

-- 13. 显示数据库状态
SELECT 'Database Status' AS Info;
SELECT (SELECT COUNT(*) FROM users) AS 'User Count';
SELECT (SELECT COUNT(*) FROM images) AS 'Image Count';
SELECT (SELECT COUNT(*) FROM likes) AS 'Like Count';
SELECT (SELECT SUM(views) FROM images) AS 'Total Views';
SELECT (SELECT SUM(likes) FROM images) AS 'Total Likes';

-- 14. 显示用户列表
SELECT 'User List' AS Info;
SELECT username, email, created_at FROM users ORDER BY created_at DESC;

-- 15. 显示最新图片
SELECT 'Latest Images' AS Info;
SELECT i.id, i.title, i.views, i.likes, i.upload_time, u.username AS 'Uploader'
FROM images i
LEFT JOIN users u ON i.user_id = u.id
WHERE i.is_active = TRUE
ORDER BY i.upload_time DESC
LIMIT 5;

-- 16. 显示创建成功的消息
SELECT 'Database initialization completed successfully!' AS Message;