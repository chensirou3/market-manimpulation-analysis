# SSH 密钥配置指南 / SSH Key Setup Guide

## 🔑 问题诊断

**当前状态**: SSH 密钥未配置，无法推送到 GitHub

**错误信息**: `Permission denied (publickey)`

**原因**: 您的 `.ssh` 目录中没有 GitHub 可用的 SSH 密钥

---

## ✅ 解决方案（两种方法）

### 方法 1: 配置 SSH 密钥（推荐，一次配置永久使用）

#### 步骤 1: 生成 SSH 密钥

在 PowerShell 中运行：

```powershell
# 生成新的 ED25519 密钥（推荐）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 或者生成 RSA 密钥（兼容性更好）
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

**提示**：
- 按 Enter 使用默认文件位置 (`C:\Users\67580\.ssh\id_ed25519`)
- 可以设置密码保护（推荐）或直接按 Enter 跳过
- 会生成两个文件：
  - `id_ed25519` (私钥，保密)
  - `id_ed25519.pub` (公钥，添加到 GitHub)

#### 步骤 2: 复制公钥

```powershell
# 显示公钥内容
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub

# 或者直接复制到剪贴板
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | Set-Clipboard
```

#### 步骤 3: 添加公钥到 GitHub

1. **访问 GitHub SSH 设置页面**
   ```
   https://github.com/settings/keys
   ```

2. **点击 "New SSH key"**

3. **填写信息**
   - Title: `Market Project - Desktop PC` (或任何你喜欢的名字)
   - Key type: `Authentication Key`
   - Key: 粘贴刚才复制的公钥内容（以 `ssh-ed25519` 或 `ssh-rsa` 开头）

4. **点击 "Add SSH key"**

#### 步骤 4: 测试 SSH 连接

```powershell
ssh -T git@github.com
```

**成功的输出**：
```
Hi chensirou3! You've successfully authenticated, but GitHub does not provide shell access.
```

#### 步骤 5: 推送到 GitHub

```powershell
cd C:\Users\67580\OneDrive\Desktop\market
git push -u origin main
```

---

### 方法 2: 使用 HTTPS 方式（临时方案）

如果您不想配置 SSH，可以改用 HTTPS：

#### 步骤 1: 更改远程仓库 URL

```powershell
# 移除当前的 SSH 远程仓库
git remote remove origin

# 添加 HTTPS 远程仓库
git remote add origin https://github.com/chensirou3/market-manimpulation-analysis.git
```

#### 步骤 2: 创建 GitHub Personal Access Token

1. **访问 GitHub Token 设置页面**
   ```
   https://github.com/settings/tokens
   ```

2. **点击 "Generate new token" → "Generate new token (classic)"**

3. **配置 Token**
   - Note: `Market Project Access`
   - Expiration: 选择有效期（建议 90 天或更长）
   - Scopes: 勾选 `repo` (完整仓库访问权限)

4. **点击 "Generate token"**

5. **复制 Token**（只显示一次，请保存好）

#### 步骤 3: 推送到 GitHub

```powershell
git push -u origin main
```

**提示**：
- Username: `chensirou3`
- Password: 粘贴刚才生成的 Token（不是 GitHub 密码）

#### 步骤 4: 保存凭据（可选）

```powershell
# 配置 Git 记住凭据
git config --global credential.helper wincred
```

下次推送时就不需要再输入 Token 了。

---

## 🎯 推荐方案对比

| 特性 | SSH 密钥 | HTTPS + Token |
|------|----------|---------------|
| 安全性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 配置难度 | 中等 | 简单 |
| 使用便利性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 多机使用 | 每台机器配置一次 | 需要保存 Token |
| 推荐度 | ✅ 推荐 | 临时方案 |

**建议**: 使用 SSH 密钥（方法 1），一次配置后永久使用，更安全更方便。

---

## 🔧 常见问题

### Q1: ssh-keygen 命令找不到

**解决方案**: 确保已安装 OpenSSH

```powershell
# 检查是否安装
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH*'

# 如果未安装，安装 OpenSSH 客户端
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
```

### Q2: 生成密钥后仍然无法连接

**可能原因**: SSH agent 未运行

**解决方案**:

```powershell
# 启动 SSH agent
Start-Service ssh-agent

# 添加密钥到 agent
ssh-add $env:USERPROFILE\.ssh\id_ed25519
```

### Q3: 已有多个 SSH 密钥，如何指定使用哪个？

**解决方案**: 创建 SSH 配置文件

```powershell
# 创建或编辑 config 文件
notepad $env:USERPROFILE\.ssh\config
```

添加以下内容：

```
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519
```

### Q4: 推送时提示 "repository not found"

**可能原因**:
1. 仓库名称拼写错误
2. 仓库不存在
3. 没有访问权限

**解决方案**:

1. **检查仓库是否存在**
   ```
   访问: https://github.com/chensirou3/market-manimpulation-analysis
   ```

2. **如果不存在，创建仓库**
   - 访问: https://github.com/new
   - Repository name: `market-manimpulation-analysis`
   - 不要初始化 README、.gitignore 或 LICENSE
   - 点击 "Create repository"

3. **重新推送**
   ```powershell
   git push -u origin main
   ```

---

## 📋 完整操作流程（SSH 方式）

```powershell
# 1. 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. 复制公钥
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | Set-Clipboard

# 3. 添加到 GitHub (在浏览器中操作)
# 访问: https://github.com/settings/keys

# 4. 测试连接
ssh -T git@github.com

# 5. 推送代码
cd C:\Users\67580\OneDrive\Desktop\market
git push -u origin main
```

---

## 📋 完整操作流程（HTTPS 方式）

```powershell
# 1. 更改为 HTTPS URL
git remote remove origin
git remote add origin https://github.com/chensirou3/market-manimpulation-analysis.git

# 2. 生成 GitHub Token (在浏览器中操作)
# 访问: https://github.com/settings/tokens

# 3. 推送代码（会提示输入用户名和密码）
git push -u origin main
# Username: chensirou3
# Password: [粘贴 Token]

# 4. 保存凭据（可选）
git config --global credential.helper wincred
```

---

## ✅ 验证推送成功

推送成功后，您应该看到类似输出：

```
Enumerating objects: 50, done.
Counting objects: 100% (50/50), done.
Delta compression using up to 8 threads
Compressing objects: 100% (45/45), done.
Writing objects: 100% (50/50), 50.00 KiB | 5.00 MiB/s, done.
Total 50 (delta 5), reused 0 (delta 0), pack-reused 0
To github.com:chensirou3/market-manimpulation-analysis.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

然后访问：
```
https://github.com/chensirou3/market-manimpulation-analysis
```

应该能看到所有文件！

---

**需要帮助？** 请按照上述步骤操作，如有问题请告诉我具体的错误信息。

