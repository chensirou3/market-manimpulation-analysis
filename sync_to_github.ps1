# Git 同步脚本 / Git Sync Script
# 用于首次将项目推送到 GitHub
# For first-time push to GitHub

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Market Manipulation Detection Toolkit" -ForegroundColor Cyan
Write-Host "Git 同步到 GitHub / Sync to GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 读取 SSH URL
$sshUrl = "git@github.com:chensirou3/market-manimpulation-analysis.git"
Write-Host "GitHub 仓库 / Repository: $sshUrl" -ForegroundColor Green
Write-Host ""

# 检查是否已经初始化
if (Test-Path ".git") {
    Write-Host "✓ Git 仓库已存在" -ForegroundColor Green
} else {
    Write-Host "初始化 Git 仓库..." -ForegroundColor Yellow
    git init
    Write-Host "✓ Git 仓库已初始化" -ForegroundColor Green
}
Write-Host ""

# 配置用户信息（如果需要）
Write-Host "配置 Git 用户信息..." -ForegroundColor Yellow
git config user.email "chensirou3@example.com"
git config user.name "chensirou3"
Write-Host "✓ 用户信息已配置" -ForegroundColor Green
Write-Host ""

# 添加所有文件
Write-Host "添加文件到暂存区..." -ForegroundColor Yellow
git add .
Write-Host "✓ 文件已添加" -ForegroundColor Green
Write-Host ""

# 显示将要提交的文件
Write-Host "将要提交的文件:" -ForegroundColor Cyan
git status --short
Write-Host ""

# 确认
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "注意事项 / Important Notes:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "✓ data/ 目录中的数据文件不会被提交" -ForegroundColor Green
Write-Host "✓ github.txt 不会被提交" -ForegroundColor Green
Write-Host "✓ __pycache__ 等缓存文件不会被提交" -ForegroundColor Green
Write-Host ""

$confirm = Read-Host "是否继续提交并推送到 GitHub? (y/n)"

if ($confirm -eq "y" -or $confirm -eq "Y") {
    # 提交
    Write-Host ""
    Write-Host "提交更改..." -ForegroundColor Yellow
    git commit -m "Initial commit: Market Manipulation Detection Toolkit

- 完整的数据处理流程 (tick → bar → features)
- 基准市场模拟 (无限/有限财富模型)
- 多维异常检测 (价量/成交量/结构)
- ManipScore 因子构建
- 回测框架与策略过滤
- 完整文档和测试
- 开发工具 (verify_setup.py, quick_start.py)

项目状态: 完成并可用
版本: 0.1.0"
    
    Write-Host "✓ 更改已提交" -ForegroundColor Green
    Write-Host ""
    
    # 添加远程仓库
    Write-Host "添加远程仓库..." -ForegroundColor Yellow
    git remote remove origin 2>$null  # 删除可能存在的旧配置
    git remote add origin $sshUrl
    Write-Host "✓ 远程仓库已添加" -ForegroundColor Green
    Write-Host ""
    
    # 推送到 GitHub
    Write-Host "推送到 GitHub..." -ForegroundColor Yellow
    Write-Host "注意: 如果这是首次推送，可能需要确认 SSH 密钥" -ForegroundColor Cyan
    Write-Host ""
    
    git push -u origin main
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "✓ 成功推送到 GitHub!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "仓库地址: https://github.com/chensirou3/market-manimpulation-analysis" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "后续更新使用:" -ForegroundColor Yellow
        Write-Host "  git add ." -ForegroundColor White
        Write-Host "  git commit -m '更新说明'" -ForegroundColor White
        Write-Host "  git push" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "✗ 推送失败" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "可能的原因:" -ForegroundColor Yellow
        Write-Host "1. SSH 密钥未配置或未添加到 GitHub" -ForegroundColor White
        Write-Host "2. 仓库不存在或无权限" -ForegroundColor White
        Write-Host "3. 网络连接问题" -ForegroundColor White
        Write-Host ""
        Write-Host "请检查:" -ForegroundColor Yellow
        Write-Host "1. SSH 密钥: ssh -T git@github.com" -ForegroundColor White
        Write-Host "2. 仓库是否已在 GitHub 上创建" -ForegroundColor White
        Write-Host ""
    }
} else {
    Write-Host ""
    Write-Host "已取消操作" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "您可以稍后手动执行:" -ForegroundColor Cyan
    Write-Host "  git add ." -ForegroundColor White
    Write-Host "  git commit -m 'Initial commit'" -ForegroundColor White
    Write-Host "  git remote add origin $sshUrl" -ForegroundColor White
    Write-Host "  git push -u origin main" -ForegroundColor White
    Write-Host ""
}

Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

