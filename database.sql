-- 1. 创建主数据库（统一命名为pic_share_db，避免混乱）
CREATE DATABASE IF NOT EXISTS pic_share_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 创建专用用户（避免重复创建报错，先判断是否存在）
CREATE USER IF NOT EXISTS 'pic_share_user'@'localhost' IDENTIFIED BY '123456'; -- 简化密码为123456，适配你的环境
GRANT ALL PRIVILEGES ON pic_share_db.* TO 'pic_share_user'@'localhost';
FLUSH PRIVILEGES;

-- 3. 切换到目标数据库
USE pic_share_db;

-- 4. 创建图片表
CREATE TABLE IF NOT EXISTS images (
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
    is_active BOOLEAN DEFAULT TRUE,
    user_id INT NULL,
    INDEX idx_user (user_id),
    INDEX idx_upload_time (upload_time),
    INDEX idx_filename (filename)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. 创建用户表（添加IF NOT EXISTS避免重复创建）
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 6. 创建标签表
CREATE TABLE IF NOT EXISTS tags (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. 创建图片-标签关联表
CREATE TABLE IF NOT EXISTS image_tags (
    image_id INT,
    tag_id INT,
    PRIMARY KEY (image_id, tag_id),
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. 插入admin用户（添加ON DUPLICATE KEY避免重复报错）
INSERT INTO users (username, email, password_hash) 
VALUES ('admin', 'admin@example.com', 'pbkdf2:sha256:150000$xxxxxxxx$xxxxxxxx') -- 替换为实际加密密码（或先用123456的加密值）
ON DUPLICATE KEY UPDATE email=email; -- 重复时不修改，避免1062报错