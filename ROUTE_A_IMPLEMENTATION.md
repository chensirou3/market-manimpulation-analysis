# 🚀 Route A: 多时间周期分析 - 实施方案

**创建时间**: 2025-11-15  
**状态**: ✅ 已实现，准备运行

---

## 📋 核心理念

### 问题诊断

**当前5分钟策略的问题**:
- ManipScore只捕捉**单根K线的异常尖刺**
- 真正的市场操纵/控盘行为是**多K线、更长时间周期**的过程
- 单根5m K线的高ManipScore ≠ "控盘周期的尾声"

### 解决方案（Route A）

**在更高时间周期重建整套框架**:
- 15分钟、30分钟、1小时K线
- 每个时间周期独立计算ManipScore
- 重新验证"极端趋势+高ManipScore→反转"规律
- 找到最符合"控盘行为"的时间周期

---

## ✅ 已实现的模块

### 1️⃣ 数据处理模块

**文件**: `src/data/bar_builder.py`

**功能**:
```python
def resample_bars_from_lower_tf(lower_bars, target_bar_size):
    """
    从低时间周期聚合到高时间周期
    
    输入: 5分钟K线
    输出: 15m/30m/1h K线
    
    聚合规则:
    - OHLC: first/max/min/last
    - N_ticks: sum (总tick数)
    - spread_mean: mean (平均价差)
    - RV: sum (实现波动率)
    """
```

**特点**:
- ✅ 支持任意时间周期
- ✅ 正确聚合微观结构特征
- ✅ 保持数据一致性

---

### 2️⃣ ManipScore模型模块

**文件**: `src/features/manipscore_model.py`

**核心类**:
```python
@dataclass
class ManipScoreModel:
    bar_size: str              # 时间周期
    feature_cols: List[str]    # 使用的特征
    regressor: LinearRegression # 拟合的模型
    scaler_X: StandardScaler   # 特征标准化
    residual_mean: float       # 残差均值
    residual_std: float        # 残差标准差
```

**核心函数**:
```python
def fit_manipscore_model(bars, bar_size):
    """
    为特定时间周期拟合ManipScore模型
    
    模型: |return| ~ f(N_ticks, spread_mean, RV, ...)
    ManipScore = (residual - mean) / std
    
    关键: 每个时间周期独立拟合，不复用5m系数
    """

def apply_manipscore(bars, model):
    """
    应用拟合好的模型计算ManipScore
    
    返回: bars with 'ManipScore' column
    """
```

**特点**:
- ✅ 每个时间周期独立拟合
- ✅ 自动检测可用特征
- ✅ 标准化处理
- ✅ z-score归一化

---

### 3️⃣ 策略模块更新

**文件**: `src/strategies/extreme_reversal.py`

**更新内容**:
```python
@dataclass
class ExtremeReversalConfig:
    bar_size: str = "5min"  # NEW: 时间周期参数
    
    # 所有窗口参数都是"K线数"，时间自动缩放
    L_past: int = 5          # 5根K线（5m=25分钟，30m=2.5小时）
    vol_window: int = 20     # 20根K线
    holding_horizon: int = 5 # 5根K线
    atr_window: int = 10     # 10根K线
    ...
```

**关键设计**:
- ✅ 所有窗口用"K线数"表示
- ✅ 时间跨度随bar_size自动缩放
- ✅ 逻辑保持一致

**示例**:
```
5分钟:  L_past=5 → 25分钟回看
15分钟: L_past=5 → 75分钟回看
30分钟: L_past=5 → 150分钟回看
1小时:  L_past=5 → 5小时回看
```

---

### 4️⃣ 实验驱动脚本

**文件**: `routeA_timeframe_study.py`

**工作流程**:

```
For each bar_size in ["5min", "15min", "30min", "60min"]:
    
    1. 构建K线
       ├─ 从5m数据聚合到目标时间周期
       └─ 计算微观结构特征
    
    2. 计算ManipScore
       ├─ 拟合该时间周期的基线模型
       └─ 计算残差z-score
    
    3. 实证分析
       ├─ 极端趋势+高ManipScore的反转概率
       ├─ 不同持有期的平均收益
       └─ 保存: routeA_reversal_stats_{bar_size}.csv
    
    4. 策略回测
       ├─ 生成信号
       ├─ 运行回测（2015-2025）
       ├─ 计算性能指标
       └─ 保存: extreme_reversal_summary_{bar_size}.md
    
    5. 保存数据
       └─ bars_{bar_size}_with_manipscore_*.csv

最后: 生成综合对比报告
    ├─ routeA_timeframe_comparison.csv
    └─ routeA_timeframe_report.md
```

---

## 📊 预期输出

### 数据文件

```
results/
├── bars_5min_with_manipscore_*.csv      # 5分钟数据（已有）
├── bars_15min_with_manipscore_*.csv     # 15分钟数据（新）
├── bars_30min_with_manipscore_*.csv     # 30分钟数据（新）
└── bars_60min_with_manipscore_*.csv     # 1小时数据（新）
```

### 分析结果

```
results/
├── routeA_reversal_stats_5min.csv       # 5m反转统计
├── routeA_reversal_stats_15min.csv      # 15m反转统计
├── routeA_reversal_stats_30min.csv      # 30m反转统计
└── routeA_reversal_stats_60min.csv      # 1h反转统计
```

**内容示例**:
```csv
bar_size,horizon,n_total,reversal_prob_combined,avg_future_ret
5min,1,262,0.52,-0.0001
5min,3,262,0.54,-0.0003
5min,5,262,0.56,-0.0005
15min,1,87,0.58,-0.0008
15min,3,87,0.61,-0.0015
...
```

### 回测结果

```
results/
├── extreme_reversal_summary_5min.md
├── extreme_reversal_summary_15min.md
├── extreme_reversal_summary_30min.md
└── extreme_reversal_summary_60min.md
```

### 综合对比

```
results/
├── routeA_timeframe_comparison.csv      # 性能对比表
└── routeA_timeframe_report.md           # 综合报告
```

**对比内容**:
```csv
bar_size,total_return,sharpe_ratio,win_rate,n_trades,reversal_prob
5min,0.03%,-0.45,37.8%,252,0.56
15min,2.5%,0.85,52.3%,89,0.61
30min,5.2%,1.35,58.7%,45,0.65
60min,3.8%,1.12,55.2%,28,0.63
```

---

## 🚀 如何运行

### 运行完整分析

```bash
python routeA_timeframe_study.py
```

**预计耗时**: 30-60分钟（取决于数据量）

**过程**:
1. 加载5分钟数据（761,279根K线）
2. 处理4个时间周期
3. 每个时间周期：
   - 聚合K线
   - 拟合ManipScore
   - 实证分析
   - 策略回测
   - 保存结果
4. 生成综合对比报告

---

## 📈 预期发现

### 假设1: 更高时间周期效果更好

**理由**: 
- 控盘行为是多K线过程
- 30m/1h更能捕捉"控盘周期"
- 减少噪音，提高信号质量

**预期**:
```
反转概率:
5min:  56% (当前)
15min: 58-60%
30min: 60-65% ⭐
60min: 58-62%
```

### 假设2: 信号数量减少但质量提高

**预期**:
```
信号数量:
5min:  262个
15min: 80-100个
30min: 40-60个 ⭐
60min: 20-30个

胜率:
5min:  38%
15min: 45-50%
30min: 55-60% ⭐
60min: 50-55%
```

### 假设3: 30分钟可能是最优时间周期

**理由**:
- 足够长以捕捉控盘行为
- 不会太长导致信号过少
- 平衡信号质量和数量

---

## 🔍 分析重点

### 查看综合对比报告

```bash
cat results/routeA_timeframe_report.md
```

**关注指标**:
1. **反转概率** - 哪个时间周期反转最明显？
2. **策略收益** - 哪个时间周期策略表现最好？
3. **Sharpe比率** - 风险调整后收益
4. **信号数量** - 是否足够交易？
5. **胜率** - 是否显著高于50%？

### 对比不同时间周期

```python
import pandas as pd

# 加载对比数据
df = pd.read_csv('results/routeA_timeframe_comparison.csv')

# 按Sharpe排序
df_sorted = df.sort_values('sharpe_ratio', ascending=False)
print(df_sorted)

# 可视化
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 收益 vs 时间周期
axes[0,0].bar(df['bar_size'], df['total_return'])
axes[0,0].set_title('Total Return by Timeframe')

# Sharpe vs 时间周期
axes[0,1].bar(df['bar_size'], df['sharpe_ratio'])
axes[0,1].set_title('Sharpe Ratio by Timeframe')

# 胜率 vs 时间周期
axes[1,0].bar(df['bar_size'], df['win_rate'])
axes[1,0].set_title('Win Rate by Timeframe')

# 信号数 vs 时间周期
axes[1,1].bar(df['bar_size'], df['n_trades'])
axes[1,1].set_title('Number of Trades by Timeframe')

plt.tight_layout()
plt.savefig('results/timeframe_comparison.png')
```

---

## 💡 下一步行动

### 立即执行

1. **运行Route A分析**
   ```bash
   python routeA_timeframe_study.py
   ```

2. **查看结果**
   - 综合对比: `results/routeA_timeframe_comparison.csv`
   - 详细报告: `results/routeA_timeframe_report.md`

3. **确定最优时间周期**
   - 哪个时间周期反转概率最高？
   - 哪个时间周期策略表现最好？
   - 信号数量是否足够？

### 后续优化

4. **在最优时间周期上优化参数**
   - 如果30m最好，在30m上运行参数优化
   - 调整L_past, holding_horizon等

5. **多时间周期组合**
   - 如果多个时间周期都有效
   - 可以组合信号（如30m+1h）

6. **Route B探索**（可选）
   - 在5m上引入"多K线异常密度"指标
   - 与Route A结果对比

---

## 🎯 成功标准

### 最低目标

- ✅ 至少一个时间周期反转概率 > 60%
- ✅ 至少一个时间周期策略Sharpe > 1.0
- ✅ 至少一个时间周期胜率 > 50%

### 理想目标

- 🎯 30m或1h反转概率 > 65%
- 🎯 策略年化收益 > 5%
- 🎯 Sharpe > 1.5
- 🎯 胜率 > 55%
- 🎯 最大回撤 < 10%

---

## 📝 技术细节

### 无前视偏差保证

- ✅ 信号生成: `exec_signal_t = raw_signal_{t-1}`
- ✅ ManipScore: 只用历史数据拟合
- ✅ 阈值计算: 基于历史分位数

### 时间缩放一致性

所有窗口参数用"K线数"表示:
```
参数         5min    15min   30min   60min
L_past=5     25min   75min   150min  300min
vol_win=20   100min  300min  600min  1200min
horizon=5    25min   75min   150min  300min
```

### 数据完整性

- ✅ 从5m聚合保证数据一致性
- ✅ 微观结构特征正确聚合
- ✅ 缺失值处理

---

**准备好了吗？开始Route A分析！** 🚀

```bash
python routeA_timeframe_study.py
```

