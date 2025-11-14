# 下一步操作指南 / Next Steps Guide

**日期**: 2025-11-14  
**状态**: ✅ 1 个月测试数据运行成功

---

## ✅ 已完成

1. ✅ 数据导入和验证 (3,338 个文件, 7.49 GB)
2. ✅ 数据格式自动适配 (ts_utc → timestamp, bid/ask → price)
3. ✅ 完整流程测试 (2024 年 1 月数据)
4. ✅ 结果保存 (results/bars_with_manipscore_2024-01-01_2024-01-31.csv)

---

## 🚀 运行完整年度数据

### 方法 1: 按季度运行 (推荐)

**优点**: 避免内存问题，可以分批处理

```bash
python run_by_quarter.py
```

这将自动处理 2024 年的 4 个季度：
- Q1: 2024-01-01 至 2024-03-31
- Q2: 2024-04-01 至 2024-06-30
- Q3: 2024-07-01 至 2024-09-30
- Q4: 2024-10-01 至 2024-12-31

**预计时间**: 每个季度 1-2 分钟，总计 5-10 分钟

**输出文件**:
- `results/bars_with_manipscore_2024-01-01_2024-03-31.csv` (Q1)
- `results/bars_with_manipscore_2024-04-01_2024-06-30.csv` (Q2)
- `results/bars_with_manipscore_2024-07-01_2024-09-30.csv` (Q3)
- `results/bars_with_manipscore_2024-10-01_2024-12-31.csv` (Q4)
- `results/summary_2024_by_quarter.csv` (汇总)

### 方法 2: 运行完整年度 (需要大内存)

```bash
python run_full_year_2024.py
```

**注意**: 需要至少 8 GB 可用内存

---

## 📊 查看结果

### 1. 使用 Python 查看

```python
import pandas as pd

# 加载结果
df = pd.read_csv('results/bars_with_manipscore_2024-01-01_2024-01-31.csv', 
                 index_col=0, parse_dates=True)

# 查看基本信息
print(df.info())
print(df.head())

# 查看 ManipScore 分布
print(df['manip_score'].describe())

# 查看高操纵分数时段
high_manip = df[df['manip_score'] > 0.7]
print(f"高操纵分数时段: {len(high_manip)} 个")
print(high_manip[['close', 'volume', 'manip_score']])
```

### 2. 使用 Jupyter Notebook

```bash
jupyter notebook notebooks/explore_data.ipynb
```

### 3. 使用 Excel

直接打开 `results/bars_with_manipscore_2024-01-01_2024-01-31.csv`

---

## 🔧 改进建议

### 1. 添加缺失的特征列

当前缺少以下特征，导致部分检测器无法完全发挥作用：

**编辑文件**: `src/data_prep/bar_aggregator.py`

在 `ticks_to_bars()` 函数中添加：

```python
# 计算 gross_volume 和 net_volume (用于对敲检测)
df_bars['gross_volume'] = df_bars['volume']
df_bars['net_volume'] = df_bars['volume'] * np.sign(df_bars['close'] - df_bars['open'])

# 计算 wick_ratio 和 body (用于极端 K 线检测)
df_bars['body'] = abs(df_bars['close'] - df_bars['open'])
df_bars['upper_wick'] = df_bars['high'] - df_bars[['open', 'close']].max(axis=1)
df_bars['lower_wick'] = df_bars[['open', 'close']].min(axis=1) - df_bars['low']
df_bars['wick_ratio'] = (df_bars['upper_wick'] + df_bars['lower_wick']) / (df_bars['body'] + 1e-8)
```

### 2. 调整参数

**编辑文件**: `src/config/config.yaml`

根据数据特点调整：

```yaml
anomaly:
  price_volume:
    window: 100  # 价量模型窗口
    threshold: 2.5  # 异常阈值
  
  volume_spike:
    lookback_days: 30  # 回看天数
    threshold: 3.0  # 突增阈值
  
  structure:
    wash_window: 20  # 对敲检测窗口
    wash_threshold: 5.0  # 对敲阈值
    wick_ratio_threshold: 3.0  # 极端 K 线阈值

manipulation_score:
  weights:
    price_volume: 0.25  # 价量异常权重
    volume_spike: 0.25  # 成交量突增权重
    structure: 0.25  # 结构异常权重
    wash_trade: 0.25  # 对敲权重
  
  filter_threshold: 0.7  # 过滤阈值
```

### 3. 可视化分析

创建可视化脚本查看结果：

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 加载数据
df = pd.read_csv('results/bars_with_manipscore_2024-01-01_2024-01-31.csv', 
                 index_col=0, parse_dates=True)

# 1. ManipScore 时间序列
plt.figure(figsize=(15, 5))
plt.plot(df.index, df['manip_score'], alpha=0.7)
plt.axhline(y=0.7, color='r', linestyle='--', label='High Risk Threshold')
plt.title('Manipulation Score Over Time')
plt.xlabel('Date')
plt.ylabel('ManipScore')
plt.legend()
plt.tight_layout()
plt.savefig('results/manipscore_timeseries.png', dpi=300)
plt.show()

# 2. 异常分数分布
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
df['pv_anomaly'].hist(bins=50, ax=axes[0, 0])
axes[0, 0].set_title('Price-Volume Anomaly Distribution')
df['vol_spike'].hist(bins=50, ax=axes[0, 1])
axes[0, 1].set_title('Volume Spike Distribution')
df['manip_score'].hist(bins=50, ax=axes[1, 0])
axes[1, 0].set_title('ManipScore Distribution')
plt.tight_layout()
plt.savefig('results/anomaly_distributions.png', dpi=300)
plt.show()

# 3. 价格 vs ManipScore
fig, ax1 = plt.subplots(figsize=(15, 6))
ax1.plot(df.index, df['close'], 'b-', alpha=0.7, label='Price')
ax1.set_xlabel('Date')
ax1.set_ylabel('Price', color='b')
ax1.tick_params(axis='y', labelcolor='b')

ax2 = ax1.twinx()
ax2.plot(df.index, df['manip_score'], 'r-', alpha=0.5, label='ManipScore')
ax2.set_ylabel('ManipScore', color='r')
ax2.tick_params(axis='y', labelcolor='r')
ax2.axhline(y=0.7, color='r', linestyle='--', alpha=0.3)

plt.title('Price vs Manipulation Score')
plt.tight_layout()
plt.savefig('results/price_vs_manipscore.png', dpi=300)
plt.show()
```

---

## 📝 常见问题

### Q1: 为什么对敲检测和极端 K 线检测没有结果？

**A**: 当前数据缺少必要的特征列 (`gross_volume`, `net_volume`, `wick_ratio`, `body`)。请参考上面的"改进建议 1"添加这些特征。

### Q2: 为什么成交量都是 2.0？

**A**: 您的数据是 quote 数据（报价数据），而非 trade 数据（成交数据）。每个 tick 的 volume 是 `bid_size + ask_size`，通常都是 1.0 + 1.0 = 2.0。这是正常的。

### Q3: 如何处理更长时间段的数据？

**A**: 使用 `run_by_quarter.py` 按季度处理，或者修改 `run_full_pipeline.py` 中的日期范围。

### Q4: 如何调整过滤阈值？

**A**: 在 `run_full_pipeline.py` 中修改 `filter_threshold` 参数：

```python
filtered_signals = apply_manipulation_filter(
    signals,
    manip_score,
    threshold=0.7,  # 修改这里
    mode='zero'
)
```

### Q5: 结果文件太大怎么办？

**A**: 可以只保存关键列：

```python
# 在 run_full_pipeline.py 中
df_to_save = df_bars[['open', 'high', 'low', 'close', 'volume', 
                       'manip_score', 'signal', 'filtered_signal']]
df_to_save.to_csv(output_file)
```

---

## 🎯 建议的工作流程

### 第 1 步: 运行完整年度数据

```bash
python run_by_quarter.py
```

### 第 2 步: 查看汇总结果

```bash
python -c "import pandas as pd; print(pd.read_csv('results/summary_2024_by_quarter.csv'))"
```

### 第 3 步: 可视化分析

```bash
jupyter notebook notebooks/explore_data.ipynb
```

### 第 4 步: 调整参数

根据分析结果调整 `src/config/config.yaml` 中的参数

### 第 5 步: 重新运行

```bash
python run_by_quarter.py
```

### 第 6 步: 对比结果

比较不同参数设置下的结果

---

## 📚 相关文档

- `README.md` - 项目概览
- `PIPELINE_SUMMARY.md` - 流程运行总结
- `DATA_VALIDATION_REPORT.md` - 数据验证报告
- `PROJECT_OVERVIEW.md` - 项目详细结构
- `docs/design_notes.md` - 设计文档

---

**祝分析顺利！如有问题，请参考文档或检查日志输出。** 🚀

