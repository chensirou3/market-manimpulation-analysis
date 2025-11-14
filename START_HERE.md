# 🚀 开始使用 / Getting Started

## 📋 当前状态

✅ **项目已完成** - 所有核心功能已实现  
✅ **SSH 已配置** - `git@github.com:chensirou3/market-manimpulation-analysis.git`  
✅ **数据目录已创建** - 正在导入数据中  
✅ **准备推送到 GitHub**

---

## 🎯 下一步操作（按顺序）

### 步骤 1: 检查 Git 状态（可选但推荐）

在 PowerShell 中运行：

```powershell
.\check_git_status.ps1
```

这会显示：
- ✅ 哪些文件会被提交
- ⚠️ 哪些文件会被忽略
- 📊 统计信息

**确认以下内容**：
- ✓ `github.txt` 被忽略
- ✓ `data/2015/`, `data/2025/` 等数据目录被忽略
- ✓ `data/README.md` 会被提交
- ✓ 所有源代码文件会被提交

---

### 步骤 2: 推送到 GitHub

在 PowerShell 中运行：

```powershell
.\sync_to_github.ps1
```

脚本会自动完成：
1. 初始化 Git 仓库
2. 配置用户信息
3. 添加文件
4. 提交更改
5. 推送到 GitHub

**预期结果**：
```
✓ 成功推送到 GitHub!
仓库地址: https://github.com/chensirou3/market-manimpulation-analysis
```

---

### 步骤 3: 验证推送成功

1. **访问 GitHub 仓库**
   ```
   https://github.com/chensirou3/market-manimpulation-analysis
   ```

2. **检查文件**
   - 应该看到约 30+ 个文件
   - README.md 会显示在首页
   - 确认 `data/` 目录只有 `README.md`

3. **确认敏感文件未泄露**
   - 搜索 `github.txt` - 应该找不到
   - 检查 `data/` - 不应该有 CSV/Parquet 文件

---

## 📚 重要文档

推送成功后，请阅读以下文档：

1. **README.md** - 项目概览和快速开始
2. **PROJECT_OVERVIEW.md** - 详细项目结构
3. **GITHUB_SYNC_GUIDE.md** - GitHub 同步完整指南
4. **DELIVERY_CHECKLIST.md** - 功能清单

---

## 🔧 如果遇到问题

### 问题 1: PowerShell 脚本无法运行

**错误**: `无法加载，因为在此系统上禁止运行脚本`

**解决方案**:
```powershell
# 临时允许脚本执行
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 然后再运行脚本
.\sync_to_github.ps1
```

### 问题 2: SSH 连接失败

**错误**: `Permission denied (publickey)`

**解决方案**:
```bash
# 测试 SSH 连接
ssh -T git@github.com

# 如果失败，检查 SSH 密钥
ls ~/.ssh/

# 如果没有密钥，生成新的
ssh-keygen -t ed25519 -C "your_email@example.com"

# 复制公钥并添加到 GitHub
cat ~/.ssh/id_ed25519.pub
```

详细解决方案请参考 `GITHUB_SYNC_GUIDE.md`

### 问题 3: 手动推送

如果脚本无法运行，手动执行：

```bash
git init
git add .
git commit -m "Initial commit: Market Manipulation Detection Toolkit"
git remote add origin git@github.com:chensirou3/market-manimpulation-analysis.git
git push -u origin main
```

---

## ✅ 推送成功后

### 后续更新流程

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

### 在新电脑上继续开发

```bash
# 1. 克隆仓库
git clone git@github.com:chensirou3/market-manimpulation-analysis.git
cd market-manimpulation-analysis

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证环境
python verify_setup.py

# 5. 开始使用
python quick_start.py
```

---

## 🎓 使用项目

### 快速验证

```bash
# 验证环境
python verify_setup.py

# 运行完整演示
python quick_start.py

# 运行市场模拟
python -m src.baseline_sim.fair_market_sim

# 运行回测流程
python -m src.backtest.pipeline
```

### 使用您的数据

1. **数据已在 data/ 目录中** ✓
2. **编辑配置文件**
   ```bash
   # 编辑 src/config/config.yaml
   # 调整参数以适应您的数据
   ```

3. **运行分析**
   ```python
   from src.data_prep.tick_loader import load_tick_data
   from src.backtest.pipeline import run_demo_backtest
   
   # 加载您的数据
   ticks = load_tick_data('YOUR_SYMBOL', start_date='2015-01-01')
   
   # 运行完整流程
   results = run_demo_backtest(symbol='YOUR_SYMBOL', use_synthetic_data=False)
   ```

---

## 📊 项目文件结构

```
market/
├── START_HERE.md              ← 你在这里
├── README.md                  ← 项目主文档
├── sync_to_github.ps1         ← GitHub 同步脚本
├── check_git_status.ps1       ← Git 状态检查
├── verify_setup.py            ← 环境验证
├── quick_start.py             ← 快速开始演示
│
├── src/                       ← 源代码
│   ├── config/config.yaml     ← 配置文件
│   ├── utils/                 ← 工具模块
│   ├── data_prep/             ← 数据处理
│   ├── baseline_sim/          ← 市场模拟
│   ├── anomaly/               ← 异常检测
│   ├── factors/               ← 因子构建
│   └── backtest/              ← 回测框架
│
├── data/                      ← 数据目录（不提交到 Git）
│   ├── README.md              ← 数据格式说明
│   ├── 2015/                  ← 您的数据
│   └── 2025/                  ← 您的数据
│
├── notebooks/                 ← Jupyter Notebooks
├── docs/                      ← 文档
└── tests/                     ← 测试
```

---

## 🎉 总结

**您现在可以**：

1. ✅ 运行 `.\check_git_status.ps1` 检查状态
2. ✅ 运行 `.\sync_to_github.ps1` 推送到 GitHub
3. ✅ 运行 `python quick_start.py` 验证项目
4. ✅ 开始使用您的数据进行分析

**项目特点**：

- ✅ 完整的操纵检测工具包
- ✅ 模块化、可扩展
- ✅ 完整文档和测试
- ✅ 多机开发支持
- ✅ 数据安全（不会提交到 Git）

---

**祝使用愉快！如有问题，请参考文档或代码注释。** 🚀

