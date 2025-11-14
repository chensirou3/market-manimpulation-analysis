# 数据检查报告 / Data Check Report

**检查日期**: 2025-11-14  
**数据目录**: `data/`

---

## ✅ 数据概览

### 📊 统计信息

- **总文件数**: 3,358 个
- **数据文件数**: 3,338 个 Parquet 文件
- **数据年份**: 2015 - 2025 (共 11 年)
- **数据总大小**: 7.49 GB (7,672.24 MB)

### 📁 文件类型分布

| 类型 | 数量 | 说明 |
|------|------|------|
| `.parquet` | 3,338 | 主要数据文件 |
| `.marker` | 19 | 标记文件 |
| `.md` | 1 | README 文档 |

---

## 📄 数据格式分析

### 示例文件

**文件**: `data/2015/01/tick/dt=2015-01-01_part-000.parquet`  
**大小**: 0.04 MB  
**行数**: 1,514 行  
**列数**: 12 列

### 数据列结构

| 列名 | 数据类型 | 说明 |
|------|----------|------|
| `ts_utc` | int64 | UTC 时间戳（毫秒） |
| `bid` | float64 | 买价 |
| `ask` | float64 | 卖价 |
| `spread` | float64 | 买卖价差 |
| `bid_size` | float64 | 买单量 |
| `ask_size` | float64 | 卖单量 |
| `source` | object | 数据来源 |
| `symbol` | object | 交易品种 |
| `recv_ts_utc` | int64 | 接收时间戳 |
| `seq` | int64 | 序列号 |
| `offsession` | bool | 是否盘后 |
| `is_spike` | bool | 是否异常波动 |

### 示例数据（前 5 行）

```
          ts_utc       bid       ask  spread  bid_size  ask_size
0  1420153208011  1.21024  1.21041  0.00017      1.00      1.00
1  1420153210261  1.21024  1.21041  0.00017      1.00      1.00
2  1420153210871  1.21024  1.21041  0.00017      1.00      1.00
3  1420153212178  1.21024  1.21041  0.00017      1.00      1.00
4  1420153212700  1.21024  1.21041  0.00017      1.00      1.00
```

---

## ⚠️ 数据格式注意事项

### 与项目预期格式的差异

项目代码期望的列名：
- ✅ `timestamp` 或 `time` → **实际**: `ts_utc` (需要映射)
- ✅ `price` → **实际**: `bid` 和 `ask` (需要计算中间价)
- ✅ `volume` → **实际**: `bid_size` 和 `ask_size` (需要聚合)

### 建议的数据适配方案

#### 方案 1: 修改数据加载器（推荐）

更新 `src/data_prep/tick_loader.py` 以适配您的数据格式：

```python
def load_tick_data(symbol, start_date=None, end_date=None, data_dir=None, file_format='parquet'):
    """
    加载 tick 数据并适配列名
    """
    # ... 原有加载逻辑 ...
    
    # 适配列名
    if 'ts_utc' in df.columns and 'timestamp' not in df.columns:
        df['timestamp'] = pd.to_datetime(df['ts_utc'], unit='ms', utc=True)
    
    # 计算中间价作为 price
    if 'bid' in df.columns and 'ask' in df.columns and 'price' not in df.columns:
        df['price'] = (df['bid'] + df['ask']) / 2
    
    # 计算总成交量
    if 'bid_size' in df.columns and 'ask_size' in df.columns and 'volume' not in df.columns:
        df['volume'] = df['bid_size'] + df['ask_size']
    
    return df
```

#### 方案 2: 创建数据预处理脚本

创建一个脚本将数据转换为标准格式后保存。

---

## 📂 数据目录结构

```
data/
├── 2015/
│   ├── 01/tick/dt=2015-01-01_part-000.parquet
│   ├── 01/tick/dt=2015-01-02_part-000.parquet
│   └── ...
├── 2016/
├── 2017/
├── ...
├── 2024/
└── 2025/
    ├── 01/
    ├── 02/
    └── ...
```

**文件命名模式**: `dt=YYYY-MM-DD_part-000.parquet`

---

## 🔍 数据质量检查

### ✅ 通过的检查

- ✅ 文件可以正常读取
- ✅ 数据格式一致（Parquet）
- ✅ 包含时间戳信息
- ✅ 包含价格信息（bid/ask）
- ✅ 包含成交量信息（bid_size/ask_size）
- ✅ 数据跨度长（11 年）
- ✅ 数据量充足（3,338 个文件，7.49 GB）

### ⚠️ 需要注意的问题

1. **列名不匹配**: 需要适配 `ts_utc` → `timestamp`, `bid/ask` → `price`
2. **没有直接的 price 列**: 需要从 bid/ask 计算中间价
3. **没有直接的 volume 列**: 需要从 bid_size/ask_size 聚合

---

## 🛠️ 使用建议

### 1. 更新数据加载器

编辑 `src/data_prep/tick_loader.py`，添加列名映射逻辑。

### 2. 更新配置文件

编辑 `src/config/config.yaml`，添加数据格式配置：

```yaml
data:
  # 列名映射
  column_mapping:
    timestamp: ts_utc
    price: mid_price  # 从 bid/ask 计算
    volume: total_size  # 从 bid_size/ask_size 计算
  
  # 时间戳单位
  timestamp_unit: ms  # 毫秒
  
  # 文件路径模式
  file_pattern: "dt={date}_part-*.parquet"
```

### 3. 测试数据加载

```python
from src.data_prep.tick_loader import load_tick_data

# 加载一天的数据测试
df = load_tick_data(
    symbol='YOUR_SYMBOL',
    start_date='2024-01-01',
    end_date='2024-01-01'
)

print(df.head())
print(df.columns)
```

### 4. 运行完整流程

```bash
# 使用真实数据运行演示
python quick_start.py --use-real-data --symbol YOUR_SYMBOL --date 2024-01-01
```

---

## 📊 数据使用示例

### 示例 1: 加载单日数据

```python
import pandas as pd
from pathlib import Path

# 读取单个文件
file_path = Path("data/2024/01/tick/dt=2024-01-01_part-000.parquet")
df = pd.read_parquet(file_path)

# 转换时间戳
df['timestamp'] = pd.to_datetime(df['ts_utc'], unit='ms', utc=True)

# 计算中间价
df['price'] = (df['bid'] + df['ask']) / 2

# 计算总量
df['volume'] = df['bid_size'] + df['ask_size']

print(df[['timestamp', 'price', 'volume', 'spread']].head())
```

### 示例 2: 加载多日数据

```python
import pandas as pd
from pathlib import Path

# 读取一个月的数据
data_dir = Path("data/2024/01/tick")
files = sorted(data_dir.glob("dt=2024-01-*.parquet"))

dfs = []
for file in files:
    df = pd.read_parquet(file)
    dfs.append(df)

# 合并
df_month = pd.concat(dfs, ignore_index=True)

print(f"总行数: {len(df_month):,}")
print(f"时间范围: {df_month['ts_utc'].min()} - {df_month['ts_utc'].max()}")
```

---

## ✅ 下一步行动

1. **更新数据加载器** - 适配您的数据格式
2. **测试数据加载** - 确保能正确读取和处理
3. **运行示例分析** - 使用真实数据测试项目功能
4. **调整参数** - 根据数据特点调整配置参数

---

## 📞 快速参考

### 数据文件位置

```
data/2024/01/tick/dt=2024-01-01_part-000.parquet
```

### 关键列

- **时间**: `ts_utc` (毫秒时间戳)
- **价格**: `bid`, `ask` (需计算中间价)
- **成交量**: `bid_size`, `ask_size` (需聚合)
- **价差**: `spread`

### 数据统计

- **文件数**: 3,338 个
- **总大小**: 7.49 GB
- **年份**: 2015-2025
- **平均文件大小**: ~2.3 MB

---

**数据状态**: ✅ **可用，需要适配列名**

**建议**: 更新 `tick_loader.py` 以适配您的数据格式，然后即可开始使用！

