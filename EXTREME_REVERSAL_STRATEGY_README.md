# 极端操纵反转策略 / Extreme Manipulation Reversal Strategy

## 📋 概述 / Overview

基于实证研究发现的量化交易策略：**当极端趋势遇到高ManipScore时，市场倾向于短期反转**。

Quantitative trading strategy based on empirical findings: **When extreme trends meet high ManipScore, markets tend to reverse in the short term**.

### 核心逻辑 / Core Logic

- **极端上涨 + 高ManipScore** → 预期反转下跌 → **做空信号**
- **极端下跌 + 高ManipScore** → 预期反转上涨 → **做多信号**

### 实证依据 / Empirical Evidence

- 极强上涨趋势(>1%) + 高ManipScore → 反转概率 **56.25%**
- 极强下跌趋势(>1%) + 高ManipScore → 反转概率 **57.50%**
- 高ManipScore后波动率增加 **~33%**

---

## 🏗️ 模块结构 / Module Structure

```
src/
├── strategies/
│   ├── trend_features.py          # 趋势强度特征计算
│   ├── extreme_reversal.py        # 信号生成逻辑
│   └── backtest_reversal.py       # 回测引擎
└── visualization/
    └── plots_reversal.py          # 可视化工具

run_extreme_reversal_strategy.py  # 主执行脚本
```

---

## 🚀 快速开始 / Quick Start

### 1. 运行策略

```bash
python run_extreme_reversal_strategy.py
```

### 2. 自定义配置

```python
from src.strategies import ExtremeReversalConfig

config = ExtremeReversalConfig(
    # 趋势参数
    L_past=5,                    # 回看5根K线
    vol_window=20,               # 波动率窗口20根K线
    q_extreme_trend=0.90,        # 极端趋势阈值（90分位数）
    min_abs_R_past=0.005,        # 最小绝对变动0.5%
    
    # ManipScore参数
    q_manip=0.90,                # 高ManipScore阈值（90分位数）
    min_manip_score=0.7,         # 最小ManipScore绝对值
    
    # 执行参数
    holding_horizon=5,           # 最大持仓5根K线
    atr_window=10,               # ATR窗口10根K线
    sl_atr_mult=0.5,             # 止损 = 0.5 * ATR
    tp_atr_mult=0.8,             # 止盈 = 0.8 * ATR
    cost_per_trade=0.0001        # 交易成本1bp
)
```

### 3. 生成信号

```python
from src.strategies import generate_extreme_reversal_signals

# bars 必须包含: 'returns' 和 'manip_score' 列
bars_with_signals = generate_extreme_reversal_signals(bars, config)

# 查看信号
print(bars_with_signals[['R_past', 'manip_score', 'exec_signal']].head())
```

### 4. 运行回测

```python
from src.strategies import run_extreme_reversal_backtest, print_backtest_summary

result = run_extreme_reversal_backtest(
    bars_with_signals,
    bars_with_signals['exec_signal'],
    config,
    initial_capital=10000.0
)

# 打印结果
print_backtest_summary(result)
```

### 5. 可视化

```python
from src.visualization import (
    plot_equity_curve,
    plot_conditional_returns,
    plot_signal_diagnostics
)

# 权益曲线
plot_equity_curve(result.equity_curve, show_drawdown=True)

# 条件收益分布
plot_conditional_returns(bars_with_signals, holding_horizon=5)

# 信号诊断
plot_signal_diagnostics(bars_with_signals)
```

---

## 📊 策略参数说明 / Parameter Guide

### 趋势强度参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `L_past` | 5 | 累计收益回看窗口（根K线） |
| `vol_window` | 20 | 滚动波动率窗口 |
| `q_extreme_trend` | 0.90 | 极端趋势分位数阈值 |
| `use_normalized_trend` | True | 使用波动率标准化的TS |
| `min_abs_R_past` | None | 可选：最小绝对R_past |

### ManipScore参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `q_manip` | 0.90 | 高ManipScore分位数阈值 |
| `min_manip_score` | None | 可选：最小ManipScore绝对值 |

### 执行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `holding_horizon` | 5 | 最大持仓时间（根K线） |
| `atr_window` | 10 | ATR计算窗口 |
| `sl_atr_mult` | 0.5 | 止损倍数（ATR的倍数） |
| `tp_atr_mult` | 0.8 | 止盈倍数（ATR的倍数） |
| `cost_per_trade` | 0.0001 | 每笔交易成本（1bp = 0.01%） |

---

## 🎯 策略特点 / Strategy Features

### ✅ 优势

1. **基于实证研究** - 56-57%的反转胜率
2. **风险可控** - ATR动态止损止盈
3. **模块化设计** - 易于扩展和优化
4. **无前视偏差** - 信号生成严格避免未来信息
5. **完整回测** - 包含交易成本、滑点等

### ⚠️ 注意事项

1. **信号稀少** - 极端趋势+高ManipScore组合较少（约1-2%）
2. **平均收益小** - 虽然胜率高，但平均收益接近0
3. **需要严格止损** - 反转失败时损失可能较大
4. **市场环境敏感** - 在极端市场（如2020）效果更好

---

## 📈 性能指标 / Performance Metrics

回测系统计算以下指标：

- **总收益** (Total Return)
- **年化收益** (Annualized Return)
- **年化波动率** (Annualized Volatility)
- **Sharpe比率** (Sharpe Ratio)
- **最大回撤** (Max Drawdown)
- **胜率** (Win Rate)
- **盈亏比** (Profit Factor)
- **平均持仓时间** (Average Holding Period)
- **退出原因分布** (Exit Reason Breakdown)

---

## 🔧 扩展建议 / Extension Ideas

### 1. 参数优化

```python
# 网格搜索最优参数
for q_trend in [0.85, 0.90, 0.95]:
    for q_manip in [0.85, 0.90, 0.95]:
        config = ExtremeReversalConfig(
            q_extreme_trend=q_trend,
            q_manip=q_manip
        )
        # 运行回测并记录结果
```

### 2. 机器学习增强

```python
# 使用逻辑回归预测反转概率
from sklearn.linear_model import LogisticRegression

features = ['R_past', 'manip_score', 'sigma', 'volume']
X = bars[features]
y = (bars['future_return_5'] * bars['R_past'] < 0).astype(int)  # 反转标签

model = LogisticRegression()
model.fit(X, y)

# 用概率替代硬阈值
bars['reversal_prob'] = model.predict_proba(X)[:, 1]
```

### 3. 多时间框架

```python
# 结合不同时间框架的信号
config_5min = ExtremeReversalConfig(L_past=5)
config_15min = ExtremeReversalConfig(L_past=15)

# 只在两个时间框架都确认时交易
```

### 4. 动态仓位管理

```python
# 根据信号强度调整仓位
position_size = min(1.0, abs(R_past) / threshold * manip_score)
```

---

## 📚 相关文档 / Related Documentation

- `趋势延续性分析报告.md` - 趋势延续性实证分析
- `高ManipScore后市场行为报告.md` - ManipScore后市场行为分析
- `回测效果报告.md` - 简单过滤策略回测结果

---

## 🤝 贡献 / Contributing

欢迎提交改进建议和bug报告！

---

**最后更新**: 2025-11-15  
**版本**: 1.0.0

