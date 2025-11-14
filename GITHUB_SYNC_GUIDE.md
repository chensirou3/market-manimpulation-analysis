# GitHub 同步指南 / GitHub Sync Guide

## 🚀 首次推送到 GitHub / First-Time Push

### 方法 1: 使用自动化脚本（推荐）

在 PowerShell 中运行：

```powershell
.\sync_to_github.ps1
```

脚本会自动完成：
1. ✅ 初始化 Git 仓库
2. ✅ 配置用户信息
3. ✅ 添加所有文件（自动排除 data/ 和敏感文件）
4. ✅ 提交更改
5. ✅ 添加远程仓库
6. ✅ 推送到 GitHub

### 方法 2: 手动执行命令

如果脚本无法运行，请手动执行以下命令：

```bash
# 1. 初始化 Git 仓库（如果还没有）
git init

# 2. 配置用户信息
git config user.email "your_email@example.com"
git config user.name "chensirou3"

# 3. 添加所有文件
git add .

# 4. 查看将要提交的文件（确认 data/ 和 github.txt 不在列表中）
git status

# 5. 提交
git commit -m "Initial commit: Market Manipulation Detection Toolkit"

# 6. 添加远程仓库
git remote add origin git@github.com:chensirou3/market-manimpulation-analysis.git

# 7. 推送到 GitHub
git push -u origin main
```

---

## ⚠️ 推送前检查清单

### 必须确认的事项：

1. **SSH 密钥已配置**
   ```bash
   # 测试 SSH 连接
   ssh -T git@github.com
   
   # 应该看到类似输出：
   # Hi chensirou3! You've successfully authenticated...
   ```

2. **GitHub 仓库已创建**
   - 仓库名称: `market-manimpulation-analysis`
   - 访问地址: https://github.com/chensirou3/market-manimpulation-analysis
   - 确保仓库为空（或准备覆盖）

3. **敏感文件不会被提交**
   ```bash
   # 检查 .gitignore 是否正确
   git status
   
   # 确认以下文件/目录不在列表中：
   # - data/ (除了 data/README.md)
   # - github.txt
   # - __pycache__/
   # - *.pyc
   ```

---

## 📊 将要提交的文件

### ✅ 会被提交的文件（约 30+ 个）

```
.gitignore
README.md
PROJECT_OVERVIEW.md
DELIVERY_CHECKLIST.md
PROJECT_STATUS.md
GITHUB_SYNC_GUIDE.md
requirements.txt
verify_setup.py
quick_start.py
sync_to_github.ps1

src/
├── config/config.yaml
├── utils/*.py
├── data_prep/*.py
├── baseline_sim/*.py
├── anomaly/*.py
├── factors/*.py
└── backtest/*.py

notebooks/*.ipynb
docs/*.md
tests/*.py
data/README.md  ← 只有这个文件会被提交
```

### ❌ 不会被提交的文件

```
github.txt          ← SSH 配置（敏感）
data/*.csv          ← 数据文件
data/*.parquet      ← 数据文件
__pycache__/        ← Python 缓存
*.pyc               ← 编译文件
.env                ← 环境变量
```

---

## 🔧 常见问题解决

### 问题 1: SSH 密钥未配置

**症状**: `Permission denied (publickey)`

**解决方案**:

```bash
# 1. 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. 复制公钥
cat ~/.ssh/id_ed25519.pub

# 3. 添加到 GitHub
# 访问: https://github.com/settings/keys
# 点击 "New SSH key"
# 粘贴公钥内容

# 4. 测试连接
ssh -T git@github.com
```

### 问题 2: 仓库不存在

**症状**: `Repository not found`

**解决方案**:

1. 访问 https://github.com/new
2. 创建新仓库: `market-manimpulation-analysis`
3. 不要初始化 README、.gitignore 或 LICENSE
4. 创建后再执行推送命令

### 问题 3: 分支名称问题

**症状**: `error: src refspec main does not match any`

**解决方案**:

```bash
# 检查当前分支
git branch

# 如果是 master 而不是 main，使用：
git push -u origin master

# 或者重命名分支为 main：
git branch -M main
git push -u origin main
```

### 问题 4: 数据文件被意外添加

**症状**: `git status` 显示 data/*.csv 文件

**解决方案**:

```bash
# 从暂存区移除
git reset HEAD data/*.csv

# 确认 .gitignore 包含
echo "*.csv" >> .gitignore
echo "*.parquet" >> .gitignore

# 重新添加
git add .
```

---

## 🔄 后续更新流程

首次推送成功后，后续更新使用：

```bash
# 1. 查看更改
git status

# 2. 添加更改
git add .

# 3. 提交
git commit -m "描述你的更改"

# 4. 推送
git push
```

### 常用提交信息示例

```bash
# 添加新功能
git commit -m "feat: 添加新的异常检测器"

# 修复 bug
git commit -m "fix: 修复 bar 聚合时间对齐问题"

# 更新文档
git commit -m "docs: 更新 README 使用说明"

# 性能优化
git commit -m "perf: 优化 manipulation score 计算速度"

# 重构代码
git commit -m "refactor: 重构数据加载模块"
```

---

## 🌐 在新电脑上克隆项目

```bash
# 1. 克隆仓库
git clone git@github.com:chensirou3/market-manimpulation-analysis.git
cd market-manimpulation-analysis

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证环境
python verify_setup.py

# 5. 添加你的数据到 data/ 目录

# 6. 开始使用
python quick_start.py
```

---

## 📝 Git 工作流最佳实践

### 提交前检查

```bash
# 查看更改的文件
git status

# 查看具体更改内容
git diff

# 查看暂存区内容
git diff --cached
```

### 分支管理（可选）

```bash
# 创建新分支开发新功能
git checkout -b feature/new-detector

# 完成后合并到主分支
git checkout main
git merge feature/new-detector

# 推送分支
git push origin feature/new-detector
```

### 查看历史

```bash
# 查看提交历史
git log --oneline

# 查看某个文件的历史
git log --follow src/factors/manipulation_score.py
```

---

## ✅ 推送成功确认

推送成功后，您应该能够：

1. **访问 GitHub 仓库**
   - https://github.com/chensirou3/market-manimpulation-analysis

2. **看到所有文件**
   - 约 30+ 个文件和目录
   - README.md 会自动显示在首页

3. **确认敏感文件未泄露**
   - 搜索 `github.txt` - 应该找不到
   - 检查 `data/` 目录 - 应该只有 README.md

4. **克隆测试**
   ```bash
   # 在另一个目录测试克隆
   cd /tmp
   git clone git@github.com:chensirou3/market-manimpulation-analysis.git test
   cd test
   ls -la
   ```

---

## 🎉 完成！

推送成功后，您的项目就可以：

- ✅ 在多台电脑上同步开发
- ✅ 版本控制和历史追踪
- ✅ 团队协作（如果需要）
- ✅ 安全备份在云端

**下次更新只需三步**：
```bash
git add .
git commit -m "更新说明"
git push
```

祝使用愉快！🚀

