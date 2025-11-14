# 全数据分析计划 / All Data Analysis Plan

**日期**: 2025-11-14  
**数据范围**: 2015-2025 (11年)  
**状态**: 准备就绪

---

## 📊 数据概览

### 可用数据

根据 `data/` 目录结构，我们有以下数据：

- **2015年**: 12个月完整数据
- **2016年**: 12个月完整数据
- **2017年**: 12个月完整数据
- **2018年**: 12个月完整数据
- **2019年**: 12个月完整数据
- **2020年**: 12个月完整数据
- **2021年**: 12个月完整数据
- **2022年**: 12个月完整数据
- **2023年**: 12个月完整数据
- **2024年**: 12个月完整数据 ✅ (已完成)
- **2025年**: 9个月数据 (1-9月)

**总计**: 约 129 个月的数据

---

## 🎯 处理策略

### 方案：按季度分批处理

由于数据量巨大，我们采用按季度分批处理的策略：

- **2015-2024年**: 10年 × 4季度 = 40个季度
- **2025年**: 3个季度 (Q1-Q3)
- **总计**: 43个季度

### 预计时间

基于2024年的处理经验：
- 每个季度约 30秒
- 43个季度 × 30秒 ≈ **22分钟**

### 内存需求

- 每个季度约 3-4 GB 内存
- 处理完成后释放
- 建议可用内存: 8 GB+

---

## 📝 执行步骤

### 步骤 1: 运行全数据分析

```bash
python run_all_data_by_quarter.py
```

这将：
1. 按季度处理 2015-2025 年的所有数据
2. 为每个季度生成一个 CSV 文件
3. 创建总汇总文件 `results/summary_all_data.csv`

### 步骤 2: 查看进度

脚本会实时显示进度：
```
处理 2015 年 Q1 (1/43)
Processing 2015 Q1 (1/43)
...
✅ 2015 Q1 处理完成
   Tick 数据: XXX,XXX 条
   K 线数据: XX,XXX 根
   高操纵分数: XXX 个
```

### 步骤 3: 查看结果

处理完成后，查看汇总：
```bash
python -c "import pandas as pd; df = pd.read_csv('results/summary_all_data.csv'); print(df)"
```

---

## 📁 预期输出

### 结果文件

将生成约 43 个 CSV 文件：

```
results/bars_with_manipscore_2015-01-01_2015-03-31.csv
results/bars_with_manipscore_2015-04-01_2015-06-30.csv
...
results/bars_with_manipscore_2025-07-01_2025-09-30.csv
```

### 汇总文件

`results/summary_all_data.csv` 包含：
- year: 年份
- quarter: 季度
- start_date: 开始日期
- end_date: 结束日期
- n_ticks: Tick 数据量
- n_bars: K 线数量
- high_manip_bars: 高操纵分数时段数量
- n_signals_original: 原始信号数量
- n_signals_filtered: 过滤后信号数量

### 预计文件大小

- 每个季度文件: 约 5-6 MB
- 43个季度: 约 **215-260 MB**
- 汇总文件: 约 10 KB

---

## 🔍 分析重点

### 1. 长期趋势分析

- **操纵行为趋势**: 2015-2025年操纵分数的变化
- **季节性模式**: 是否存在季节性操纵行为
- **年度对比**: 哪些年份操纵行为最严重

### 2. 异常检测效果

- **价量异常**: 11年间的分布
- **成交量突增**: 长期模式
- **对敲行为**: 历史趋势
- **极端K线**: 频率变化

### 3. 策略性能

- **长期回测**: 11年的策略表现
- **过滤效果**: 操纵过滤的长期价值
- **风险调整收益**: Sharpe比率的历史表现

---

## 💡 后续分析建议

### 1. 时间序列分析

```python
import pandas as pd
import matplotlib.pyplot as plt

# 加载汇总数据
df = pd.read_csv('results/summary_all_data.csv')

# 按年份汇总
yearly = df.groupby('year').agg({
    'n_ticks': 'sum',
    'n_bars': 'sum',
    'high_manip_bars': 'sum'
}).reset_index()

# 绘制趋势图
fig, axes = plt.subplots(3, 1, figsize=(15, 12))

axes[0].plot(yearly['year'], yearly['n_ticks'], marker='o')
axes[0].set_title('Tick Data Volume Over Years')
axes[0].set_ylabel('Number of Ticks')

axes[1].plot(yearly['year'], yearly['n_bars'], marker='o')
axes[1].set_title('Bar Data Volume Over Years')
axes[1].set_ylabel('Number of Bars')

axes[2].plot(yearly['year'], yearly['high_manip_bars'], marker='o', color='red')
axes[2].set_title('High Manipulation Periods Over Years')
axes[2].set_ylabel('Number of High-Risk Bars')
axes[2].set_xlabel('Year')

plt.tight_layout()
plt.savefig('results/yearly_trends.png', dpi=300)
plt.show()
```

### 2. 季节性分析

```python
# 按季度汇总
quarterly = df.groupby('quarter').agg({
    'high_manip_bars': 'mean',
    'n_bars': 'mean'
}).reset_index()

quarterly['manip_rate'] = quarterly['high_manip_bars'] / quarterly['n_bars'] * 100

print("季度平均操纵率:")
print(quarterly[['quarter', 'manip_rate']])
```

### 3. 详细时段分析

```python
# 加载特定年份的详细数据
df_2020 = pd.read_csv('results/bars_with_manipscore_2020-01-01_2020-03-31.csv', 
                      index_col=0, parse_dates=True)

# 分析高操纵时段
high_manip = df_2020[df_2020['manip_score'] > 0.7]
print(f"2020 Q1 高操纵时段: {len(high_manip)} 个")
print(high_manip[['close', 'volume', 'wash_index', 'wick_ratio', 'manip_score']].describe())
```

---

## ⚠️ 注意事项

### 1. 处理时间

- 全部43个季度预计需要 **20-25分钟**
- 请确保电脑不会休眠
- 建议在空闲时间运行

### 2. 磁盘空间

- 确保至少有 **500 MB** 可用空间
- 结果文件约 260 MB
- 临时文件可能占用额外空间

### 3. 内存使用

- 每个季度处理时约占用 3-4 GB 内存
- 处理完成后会释放
- 如果内存不足，脚本会自动跳过失败的季度

### 4. 中断恢复

- 如果处理中断，可以重新运行脚本
- 已存在的文件会被覆盖
- 建议备份重要结果

---

## ✅ 准备就绪

所有脚本和工具已准备完毕：

- ✅ `run_all_data_by_quarter.py` - 全数据按季度处理脚本
- ✅ `run_full_pipeline.py` - 完整流程脚本
- ✅ 特征已更新 (gross_volume, net_volume, wick_ratio等)
- ✅ 数据已验证 (2015-2025年)

**准备开始全数据分析！** 🚀

---

**下一步**: 运行 `python run_all_data_by_quarter.py` 开始处理

