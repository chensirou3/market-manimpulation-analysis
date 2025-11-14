# 检查 Git 状态脚本
# 用于确认哪些文件会被提交，哪些会被忽略

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Git 状态检查 / Git Status Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 初始化 Git（如果需要）
if (-not (Test-Path ".git")) {
    Write-Host "初始化 Git 仓库..." -ForegroundColor Yellow
    git init
    Write-Host ""
}

# 添加所有文件到暂存区
Write-Host "添加文件到暂存区..." -ForegroundColor Yellow
git add .
Write-Host ""

# 显示将要提交的文件
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ 将要提交的文件:" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
git status --short | Where-Object { $_ -match "^A" }
Write-Host ""

# 显示被忽略的文件（示例）
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "⚠️  被 .gitignore 忽略的文件（示例）:" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow

# 检查关键文件是否被忽略
$filesToCheck = @(
    "github.txt",
    "data/2015",
    "data/2025",
    "__pycache__"
)

foreach ($file in $filesToCheck) {
    if (Test-Path $file) {
        $status = git check-ignore $file 2>$null
        if ($status) {
            Write-Host "✓ $file - 已忽略" -ForegroundColor Green
        } else {
            Write-Host "✗ $file - 未忽略（警告！）" -ForegroundColor Red
        }
    }
}

Write-Host ""

# 检查 data/README.md 是否会被提交
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "特殊检查:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (Test-Path "data/README.md") {
    $status = git check-ignore "data/README.md" 2>$null
    if (-not $status) {
        Write-Host "✓ data/README.md - 会被提交（正确）" -ForegroundColor Green
    } else {
        Write-Host "✗ data/README.md - 被忽略（错误！）" -ForegroundColor Red
    }
}

Write-Host ""

# 统计
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "统计信息:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$stagedFiles = git diff --cached --name-only
$fileCount = ($stagedFiles | Measure-Object).Count

Write-Host "将要提交的文件数量: $fileCount" -ForegroundColor White
Write-Host ""

# 显示文件列表
Write-Host "完整文件列表:" -ForegroundColor Cyan
git diff --cached --name-only | ForEach-Object {
    Write-Host "  $_" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "检查完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "如果一切正常，可以运行:" -ForegroundColor Yellow
Write-Host "  .\sync_to_github.ps1" -ForegroundColor White
Write-Host ""

