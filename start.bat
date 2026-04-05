@echo off
chcp 65001 >nul
echo ====================================
echo 校园众筹平台 - 启动脚本
echo ====================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [1/3] 检查依赖...
pip show Flask >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [2/3] 准备启动应用...
echo.
echo 应用将在 http://127.0.0.1:5000 启动
echo.
echo 默认管理员账号: admin
echo 默认管理员密码: admin123
echo.
echo [3/3] 启动中...
echo ====================================
echo.

REM 启动Flask应用
python app.py

pause
