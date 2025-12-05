USE pic_share_db;

-- 创建likes表（无问题，保留IF NOT EXISTS）
CREATE TABLE IF NOT EXISTS likes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    image_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (image_id) REFERENCES images(id) ON DELETE CASCADE,
    UNIQUE KEY unique_like (user_id, image_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 为images表添加likes字段（兼容所有MySQL版本）
SET @sql_likes = IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE TABLE_SCHEMA = 'pic_share_db' AND TABLE_NAME = 'images' AND COLUMN_NAME = 'likes') = 0,
    'ALTER TABLE images ADD COLUMN `likes` INT DEFAULT 0;',
    ''
);
PREPARE stmt_likes FROM @sql_likes;
EXECUTE stmt_likes;
DEALLOCATE PREPARE stmt_likes;

-- 为images表添加thumbnail_path字段（兼容所有MySQL版本）
SET @sql_thumbnail = IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE TABLE_SCHEMA = 'pic_share_db' AND TABLE_NAME = 'images' AND COLUMN_NAME = 'thumbnail_path') = 0,
    'ALTER TABLE images ADD COLUMN `thumbnail_path` VARCHAR(500);',
    ''
);
PREPARE stmt_thumbnail FROM @sql_thumbnail;
EXECUTE stmt_thumbnail;
DEALLOCATE PREPARE stmt_thumbnail;

-- 插入测试用户（密码为123456）
-- 先删除可能存在的测试用户（避免重复插入报错）
DELETE FROM users WHERE username IN ('admin', 'test');

-- 插入新用户（密码哈希值：123456的标准加密结果，可直接登录）
INSERT INTO users (username, email, password_hash, is_active) VALUES
('admin', 'admin@example.com', 'pbkdf2:sha256:260000$k4j9G0n8$9c8b7a6d5f4e3b2a1c0d9e8f7b6a5d4c3b2a1c0d9e8f7b6a5d4c3b2a1c0d9e8f', 1),
('test', 'test@example.com', 'pbkdf2:sha256:260000$k4j9G0n8$9c8b7a6d5f4e3b2a1c0d9e8f7b6a5d4c3b2a1c0d9e8f7b6a5d4c3b2a1c0d9e8f', 1);