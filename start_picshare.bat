@echo off
chcp 65001
echo 正在启动PicShare图片分享网站...
cd /d "%~dp0"
call venv\Scripts\activate
python app.py
pause