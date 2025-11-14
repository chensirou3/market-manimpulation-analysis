@echo off
REM Git 同步脚本 (批处理版本)
REM 如果 PowerShell 脚本无法运行，使用这个

echo ========================================
echo Market Manipulation Detection Toolkit
echo Git 同步到 GitHub
echo ========================================
echo.

REM 检查 Git 是否安装
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] Git 未安装或不在 PATH 中
    echo 请从 https://git-scm.com/ 下载安装 Git
    pause
    exit /b 1
)

REM 初始化 Git 仓库
if not exist ".git" (
    echo 初始化 Git 仓库...
    git init
    echo.
)

REM 配置用户信息
echo 配置 Git 用户信息...
git config user.email "chensirou3@example.com"
git config user.name "chensirou3"
echo.

REM 添加文件
echo 添加文件到暂存区...
git add .
echo.

REM 显示状态
echo 将要提交的文件:
git status --short
echo.

REM 确认
echo ========================================
echo 注意事项:
echo ========================================
echo [OK] data/ 目录中的数据文件不会被提交
echo [OK] github.txt 不会被提交
echo [OK] __pycache__ 等缓存文件不会被提交
echo.

set /p confirm="是否继续提交并推送到 GitHub? (y/n): "

if /i "%confirm%" NEQ "y" (
    echo.
    echo 已取消操作
    echo.
    pause
    exit /b 0
)

REM 提交
echo.
echo 提交更改...
git commit -m "Initial commit: Market Manipulation Detection Toolkit"
echo.

REM 添加远程仓库
echo 添加远程仓库...
git remote remove origin 2>nul
git remote add origin git@github.com:chensirou3/market-manimpulation-analysis.git
echo.

REM 推送
echo 推送到 GitHub...
echo 注意: 如果这是首次推送，可能需要确认 SSH 密钥
echo.

git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo [成功] 成功推送到 GitHub!
    echo ========================================
    echo.
    echo 仓库地址: https://github.com/chensirou3/market-manimpulation-analysis
    echo.
    echo 后续更新使用:
    echo   git add .
    echo   git commit -m "更新说明"
    echo   git push
    echo.
) else (
    echo.
    echo ========================================
    echo [失败] 推送失败
    echo ========================================
    echo.
    echo 可能的原因:
    echo 1. SSH 密钥未配置或未添加到 GitHub
    echo 2. 仓库不存在或无权限
    echo 3. 网络连接问题
    echo.
    echo 请检查:
    echo 1. SSH 密钥: ssh -T git@github.com
    echo 2. 仓库是否已在 GitHub 上创建
    echo.
)

pause

