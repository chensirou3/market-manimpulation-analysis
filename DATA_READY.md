# 🎉 数据已就绪！/ Data Ready!

**日期**: 2025-11-14  
**状态**: ✅ **数据已验证，项目可以使用**

---

## ✅ 完成情况

### 1. 数据导入 ✅

- ✅ 3,338 个 Parquet 文件已导入
- ✅ 总大小: 7.49 GB
- ✅ 年份范围: 2015-2025 (11 年)
- ✅ 交易品种: XAUUSD (黄金/美元)

### 2. 数据验证 ✅

- ✅ 所有测试通过 (4/4)
- ✅ 数据可以正常加载
- ✅ 数据质量良好 (无缺失值)
- ✅ 时间序列连续

### 3. 代码适配 ✅

- ✅ `tick_loader.py` 已更新
- ✅ 支持您的数据格式 (ts_utc, bid/ask, bid_size/ask_size)
- ✅ 自动列名映射
- ✅ 时区处理正确

---

## 📊 数据概览

### 示例数据 (2024-01-02)

```
                         timestamp      price  volume    bid    ask  spread
0 2024-01-02 00:00:00.130000+00:00  2062.7050     2.0  2062.45  2062.96  0.51
1 2024-01-02 00:00:00.181000+00:00  2062.7050     2.0  2062.45  2062.96  0.51
2 2024-01-02 00:00:00.232000+00:00  2062.7050     2.0  2062.45  2062.96  0.51
```

### 数据统计

- **每日数据量**: 10-16 万条 tick
- **平均时间间隔**: 0.63 秒
- **价格范围**: 2055-2079 (2024-01-02)
- **成交量**: 固定为 2.0 (bid_size + ask_size)

---

## 🚀 快速开始

### 方法 1: 运行快速演示

```bash
python quick_start.py
```

这将运行完整的工作流程：
1. 加载数据
2. 聚合为 K 线
3. 异常检测
4. 计算 ManipScore 因子
5. 策略过滤
6. 性能对比

### 方法 2: 加载数据进行探索

```python
from src.data_prep.tick_loader import load_tick_data

# 加载一天的数据
df = load_tick_data(start_date='2024-01-02', end_date='2024-01-02')

print(f"加载了 {len(df):,} 条 tick 数据")
print(df.head())
print(df.describe())
```

### 方法 3: 使用 Jupyter Notebook

```bash
jupyter notebook notebooks/explore_data.ipynb
```

在 notebook 中：
```python
# 加载真实数据
from src.data_prep.tick_loader import load_tick_data

df = load_tick_data(start_date='2024-01-02', end_date='2024-01-02')

# 可视化
import matplotlib.pyplot as plt

df.set_index('timestamp')['price'].plot(figsize=(15, 5))
plt.title('XAUUSD Tick Price - 2024-01-02')
plt.show()
```

---

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| **DATA_VALIDATION_REPORT.md** | 详细的数据验证报告 ⭐ |
| **DATA_CHECK_REPORT.md** | 数据格式和适配说明 |
| **README.md** | 项目总体说明 |
| **START_HERE.md** | 快速开始指南 |
| **data/README.md** | 数据格式文档 |

---

## 🔧 数据加载 API

### 基本用法

```python
from src.data_prep.tick_loader import load_tick_data

# 加载单日数据
df = load_tick_data(
    start_date='2024-01-02',
    end_date='2024-01-02'
)

# 加载日期范围
df = load_tick_data(
    start_date='2024-01-01',
    end_date='2024-01-31'
)
```

### 返回的 DataFrame 列

| 列名 | 类型 | 说明 |
|------|------|------|
| `timestamp` | datetime64[ns, UTC] | 时间戳 |
| `price` | float64 | 中间价 (bid+ask)/2 |
| `volume` | float64 | 总量 (bid_size+ask_size) |
| `bid` | float64 | 买价 |
| `ask` | float64 | 卖价 |
| `spread` | float64 | 价差 |
| `bid_size` | float64 | 买单量 |
| `ask_size` | float64 | 卖单量 |
| `source` | object | 数据来源 |
| `symbol` | object | 品种 |
| `offsession` | bool | 是否盘后 |
| `is_spike` | bool | 是否异常 |

---

## 📈 数据聚合

### 聚合为 K 线

```python
from src.data_prep.bar_aggregator import ticks_to_bars

# 聚合为 5 分钟 K 线
bars_5min = ticks_to_bars(df, timeframe='5min', compute_features=True)

# 聚合为 1 小时 K 线
bars_1h = ticks_to_bars(df, timeframe='1h', compute_features=True)

# 查看结果
print(bars_5min.head())
print(bars_5min.columns)
```

### 可用的时间周期

- `'1min'` - 1 分钟
- `'5min'` - 5 分钟
- `'15min'` - 15 分钟
- `'30min'` - 30 分钟
- `'1h'` - 1 小时
- `'4h'` - 4 小时
- `'1d'` - 1 天

---

## 🎯 下一步建议

### 1. 探索数据 (推荐首先做)

```bash
# 运行测试脚本查看数据
python test_data_loading.py

# 或使用 Jupyter Notebook
jupyter notebook notebooks/explore_data.ipynb
```

### 2. 运行完整流程

```bash
# 运行快速演示
python quick_start.py
```

### 3. 测试异常检测

```python
from src.data_prep.tick_loader import load_tick_data
from src.data_prep.bar_aggregator import ticks_to_bars
from src.anomaly.price_volume_anomaly import detect_price_volume_anomaly

# 加载数据
df_ticks = load_tick_data(start_date='2024-01-02', end_date='2024-01-02')

# 聚合为 K 线
df_bars = ticks_to_bars(df_ticks, timeframe='5min')

# 检测异常
anomaly_scores = detect_price_volume_anomaly(df_bars)

print(f"检测到 {(anomaly_scores > 2).sum()} 个异常点")
```

### 4. 计算 ManipScore 因子

```python
from src.factors.manipulation_score import compute_manipulation_score

# 计算操纵分数
manip_score = compute_manipulation_score(df_bars)

# 查看高分时段
high_score = manip_score[manip_score > 0.7]
print(f"高操纵嫌疑时段: {len(high_score)} 个")
```

### 5. 回测策略

```python
from src.backtest.interfaces import apply_manipulation_filter, compare_strategies

# 生成模拟信号 (实际使用时替换为您的策略信号)
signals = (df_bars['close'] > df_bars['close'].shift(1)).astype(int)

# 应用操纵过滤
filtered_signals = apply_manipulation_filter(
    signals, 
    manip_score, 
    threshold=0.7, 
    mode='zero'
)

# 对比性能
comparison = compare_strategies(
    df_bars, 
    signals, 
    filtered_signals
)

print(comparison)
```

---

## ✅ 检查清单

在开始使用前，确认以下项目：

- [x] 数据已导入 (3,338 个文件)
- [x] 数据已验证 (所有测试通过)
- [x] 代码已适配 (tick_loader.py 已更新)
- [x] 测试脚本运行成功 (test_data_loading.py)
- [ ] 已阅读 DATA_VALIDATION_REPORT.md
- [ ] 已运行 quick_start.py
- [ ] 已探索数据 (Jupyter Notebook)

---

## 🎊 准备就绪！

**您的数据已完全就绪，可以开始使用项目进行交易操纵检测分析！**

### 推荐的第一步

```bash
# 1. 查看数据验证报告
cat DATA_VALIDATION_REPORT.md

# 2. 运行快速演示
python quick_start.py

# 3. 探索数据
jupyter notebook notebooks/explore_data.ipynb
```

---

**祝使用愉快！** 🚀

如有任何问题，请参考文档或查看代码注释。

