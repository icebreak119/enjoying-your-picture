# PicShare - 图片分享网站

一个使用 Flask 构建的简单图片分享网站。

## 功能特点
- ✅ 用户注册/登录
- ✅ 图片上传
- ✅ 图片展示（瀑布流布局）
- ✅ 点赞功能
- ✅ 响应式设计（支持手机/电脑）

## 技术栈
- **后端**: Python + Flask
- **前端**: HTML5 + CSS3 + Bootstrap 5
- **数据库**: 内存存储（开发版）
- **部署**: Railway.app

## 快速开始

### 1. 本地运行
```bash
# 克隆项目
git clone https://github.com/你的用户名/my-picshare.git

# 进入项目目录
cd my-picshare

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境（Windows）
venv\Scripts\activate
# 或 Mac/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 运行网站
python app.py