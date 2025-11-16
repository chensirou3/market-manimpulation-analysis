"""
市场操纵检测策略 - 独立可运行示例

这是一个完全独立的脚本，包含所有必要的代码，可以直接运行。
不依赖任何自定义模块，只需要标准的Python库。

使用方法:
    python strategy_example_standalone.py

输入数据格式:
    CSV文件，包含列: timestamp, open, high, low, close
    或者: timestamp, close (最小要求)
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from dataclasses import dataclass
from typing import Optional, List
import warnings
warnings.filterwarnings('ignore')


# ==================== 配置类 ====================
@dataclass
class StrategyConfig:
    """策略配置参数"""
    bar_size: str = "60min"
    L_past: int = 5              # 回看窗口
    vol_window: int = 20         # 波动率窗口
    q_extreme_trend: float = 0.9 # 极端趋势分位数
    L_future: int = 5            # 前瞻窗口（仅用于训练）
    q_manip: float = 0.9         # 高操纵分位数
    holding_horizon: int = 5     # 最大持仓时间（bar数）
    atr_window: int = 10         # ATR窗口
    sl_atr_mult: float = 999.0   # 止损倍数（999=不使用）
    tp_atr_mult: float = 999.0   # 止盈倍数（999=不使用）
    cost_per_trade: float = 0.0007  # 交易成本（7bp）


@dataclass
class Trade:
    """交易记录"""
    entry_time: pd.Timestamp
    entry_price: float
    direction: int  # 1=多, -1=空
    entry_bar: int
    sl_price: float
    tp_price: float
    exit_time: Optional[pd.Timestamp] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None


# ==================== 特征工程 ====================
def compute_log_returns(bars):
    """计算对数收益率"""
    bars = bars.copy()
    bars['log_return'] = np.log(bars['close'] / bars['close'].shift(1))
    return bars


def compute_volatility(bars, window=20):
    """计算滚动波动率"""
    bars = bars.copy()
    bars['sigma'] = bars['log_return'].rolling(window=window).std()
    
    # 前向填充缺失值
    bars['sigma'] = bars['sigma'].ffill()
    
    # 如果仍有缺失，使用全局标准差
    if bars['sigma'].isna().any():
        global_std = bars['log_return'].std()
        bars['sigma'] = bars['sigma'].fillna(global_std)
    
    return bars


def compute_trend_strength(bars, L_past=5, vol_window=20):
    """计算趋势强度 (TS)"""
    bars = bars.copy()
    
    # 对数收益率
    bars = compute_log_returns(bars)
    
    # 波动率
    bars = compute_volatility(bars, window=vol_window)
    
    # 累计收益
    bars['R_past'] = bars['log_return'].rolling(window=L_past).sum()
    
    # 趋势强度
    bars['TS'] = bars['R_past'] / bars['sigma']
    
    # 处理无穷大和NaN
    bars['TS'] = bars['TS'].replace([np.inf, -np.inf], np.nan)
    bars['TS'] = bars['TS'].fillna(0)
    
    return bars


def fit_manipscore_model(bars, L_past=5, vol_window=20):
    """
    拟合ManipScore模型

    ✅ 正确实现: 使用当前bar的绝对收益作为目标，避免前视偏差

    步骤:
    1. 计算趋势强度特征
    2. 计算当前bar的绝对收益（目标变量）
    3. 线性回归: abs_ret ~ R_past + sigma
    4. 计算残差并标准化得到ManipScore
    """
    bars = bars.copy()

    # 计算特征
    bars = compute_trend_strength(bars, L_past, vol_window)

    # ✅ 计算当前bar的绝对收益 (不使用未来数据)
    bars['abs_ret'] = bars['log_return'].abs()

    # 准备回归数据
    valid_mask = bars[['R_past', 'sigma', 'abs_ret']].notna().all(axis=1)

    if valid_mask.sum() < 100:
        raise ValueError(f"有效数据点不足: {valid_mask.sum()}, 需要至少100个")

    X = bars.loc[valid_mask, ['R_past', 'sigma']].values
    y = bars.loc[valid_mask, 'abs_ret'].values  # ✅ 使用当前bar的绝对收益

    # 拟合线性回归
    model = LinearRegression()
    model.fit(X, y)

    # 计算残差
    y_pred = model.predict(X)
    residuals = y - y_pred

    # 标准化残差 → ManipScore
    manip_score = (residuals - residuals.mean()) / residuals.std()

    # 填充到原始DataFrame
    bars.loc[valid_mask, 'ManipScore'] = manip_score
    bars['ManipScore'] = bars['ManipScore'].fillna(0)

    print(f"ManipScore模型拟合完成:")
    print(f"  - 系数: α={model.intercept_:.6f}, β1={model.coef_[0]:.6f}, β2={model.coef_[1]:.6f}")
    print(f"  - ManipScore均值: {bars['ManipScore'].mean():.6f}")
    print(f"  - ManipScore标准差: {bars['ManipScore'].std():.6f}")

    return bars, model


# ==================== 信号生成 ====================
def generate_asymmetric_signals(bars, config):
    """
    生成非对称策略信号
    
    规则:
    - 极端上涨 + 高操纵 → 做多（延续）
    - 极端下跌 + 高操纵 → 做多（反转）
    """
    bars = bars.copy()
    
    # 确保有TS和ManipScore
    if 'TS' not in bars.columns:
        bars = compute_trend_strength(bars, config.L_past, config.vol_window)
    
    # 计算极端趋势阈值
    threshold_ts = bars['TS'].abs().quantile(config.q_extreme_trend)
    extreme_up = bars['TS'] > threshold_ts
    extreme_down = bars['TS'] < -threshold_ts
    
    # 计算高操纵阈值
    threshold_manip = bars['ManipScore'].quantile(config.q_manip)
    high_manip = bars['ManipScore'] > threshold_manip
    
    # 生成信号
    signals = pd.DataFrame(index=bars.index)
    signals['signal'] = 0
    
    # 极端上涨 + 高操纵 → 做多
    signals.loc[extreme_up & high_manip, 'signal'] = 1
    
    # 极端下跌 + 高操纵 → 做多
    signals.loc[extreme_down & high_manip, 'signal'] = 1
    
    # 延迟1个bar（避免前视偏差）
    signals['signal'] = signals['signal'].shift(1).fillna(0).astype(int)
    
    print(f"\n信号生成完成:")
    print(f"  - 极端趋势阈值: {threshold_ts:.4f}")
    print(f"  - 高操纵阈值: {threshold_manip:.4f}")
    print(f"  - 信号数量: {signals['signal'].sum()}")
    print(f"  - 信号频率: {signals['signal'].mean()*100:.2f}%")
    
    return signals


# ==================== ATR计算 ====================
def compute_atr(bars, window=10):
    """计算ATR (Average True Range)"""
    # 如果没有high/low，使用close的波动作为替代
    if 'high' not in bars.columns or 'low' not in bars.columns:
        # 使用close的滚动极值作为high/low的近似
        bars['high'] = bars['close'].rolling(window=3).max()
        bars['low'] = bars['close'].rolling(window=3).min()
        bars['high'] = bars['high'].fillna(bars['close'])
        bars['low'] = bars['low'].fillna(bars['close'])
    
    # 计算True Range
    high_low = bars['high'] - bars['low']
    high_close = (bars['high'] - bars['close'].shift(1)).abs()
    low_close = (bars['low'] - bars['close'].shift(1)).abs()
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    
    # 计算ATR
    atr = tr.rolling(window=window).mean()
    
    # 填充缺失值
    atr = atr.ffill().bfill()
    
    # 设置最小ATR（防止除零）
    min_atr = bars['close'].mean() * 0.001  # 至少0.1%
    atr = atr.clip(lower=min_atr)
    
    return atr


# ==================== 回测引擎 ====================
def run_backtest(bars, signals, config, initial_capital=10000):
    """
    运行回测
    
    返回:
        dict: {
            'trades': List[Trade],
            'equity_curve': pd.Series,
            'stats': dict
        }
    """
    print(f"\n开始回测...")
    print(f"  - 初始资金: ${initial_capital:,.2f}")
    print(f"  - 交易成本: {config.cost_per_trade*100:.2f}%")
    
    equity = initial_capital
    position = None
    trades = []
    equity_curve = []
    
    # 计算ATR
    atr = compute_atr(bars, config.atr_window)
    
    # 遍历每个bar
    for t in range(len(bars)):
        # 记录权益
        equity_curve.append(equity)
        
        # 检查出场
        if position is not None:
            current_price = bars['close'].iloc[t]
            bars_held = t - position.entry_bar
            
            exit_reason = None
            exit_price = None
            
            # 检查止损
            if config.sl_atr_mult < 100 and current_price <= position.sl_price:
                exit_reason = 'SL'
                exit_price = position.sl_price
            
            # 检查止盈
            elif config.tp_atr_mult < 100 and current_price >= position.tp_price:
                exit_reason = 'TP'
                exit_price = position.tp_price
            
            # 检查时间止损
            elif bars_held >= config.holding_horizon:
                exit_reason = 'TIME'
                exit_price = current_price
            
            # 执行出场
            if exit_reason:
                # 计算收益
                pnl_pct = (exit_price - position.entry_price) / position.entry_price
                
                # 扣除交易成本
                pnl_pct -= config.cost_per_trade
                
                # 更新交易记录
                position.exit_time = bars.index[t]
                position.exit_price = exit_price
                position.exit_reason = exit_reason
                position.pnl_pct = pnl_pct
                position.pnl = equity * pnl_pct
                
                # 更新权益
                equity += position.pnl
                
                # 保存交易
                trades.append(position)
                position = None
        
        # 检查入场
        if position is None and signals['signal'].iloc[t] == 1:
            entry_price = bars['close'].iloc[t]
            
            # 计算止损止盈价格
            current_atr = atr.iloc[t]
            sl_price = entry_price - config.sl_atr_mult * current_atr
            tp_price = entry_price + config.tp_atr_mult * current_atr
            
            # 创建交易
            position = Trade(
                entry_time=bars.index[t],
                entry_price=entry_price,
                direction=1,
                entry_bar=t,
                sl_price=sl_price,
                tp_price=tp_price
            )
    
    # 如果最后还有持仓，强制平仓
    if position is not None:
        exit_price = bars['close'].iloc[-1]
        pnl_pct = (exit_price - position.entry_price) / position.entry_price - config.cost_per_trade
        position.exit_time = bars.index[-1]
        position.exit_price = exit_price
        position.exit_reason = 'END'
        position.pnl_pct = pnl_pct
        position.pnl = equity * pnl_pct
        equity += position.pnl
        trades.append(position)
    
    # 构建权益曲线
    equity_curve = pd.Series(equity_curve, index=bars.index)
    
    # 计算统计指标
    if len(trades) > 0:
        total_return = (equity - initial_capital) / initial_capital
        
        # 计算收益率序列
        returns = equity_curve.pct_change().dropna()
        
        # Sharpe比率（年化）
        if returns.std() > 0:
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 最大回撤
        cummax = equity_curve.cummax()
        drawdown = (equity_curve - cummax) / cummax
        max_drawdown = drawdown.min()
        
        # 胜率
        winning_trades = [t for t in trades if t.pnl > 0]
        win_rate = len(winning_trades) / len(trades)
        
        # 平均盈亏
        avg_win = np.mean([t.pnl_pct for t in winning_trades]) if winning_trades else 0
        losing_trades = [t for t in trades if t.pnl <= 0]
        avg_loss = np.mean([t.pnl_pct for t in losing_trades]) if losing_trades else 0
        
        # 利润因子
        total_wins = sum([t.pnl for t in winning_trades])
        total_losses = abs(sum([t.pnl for t in losing_trades]))
        profit_factor = total_wins / total_losses if total_losses > 0 else np.inf
        
        # 年化收益
        years = (bars.index[-1] - bars.index[0]).days / 365.25
        ann_return = ((1 + total_return) ** (1/years) - 1) if years > 0 else 0
        
        stats = {
            'total_return': total_return,
            'ann_return': ann_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'num_trades': len(trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'final_equity': equity
        }
    else:
        stats = {
            'total_return': 0,
            'ann_return': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'num_trades': 0,
            'win_rate': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'final_equity': initial_capital
        }
    
    return {
        'trades': trades,
        'equity_curve': equity_curve,
        'stats': stats
    }


# ==================== 主函数 ====================
def main():
    """主函数"""
    print("="*60)
    print("市场操纵检测策略 - 独立示例")
    print("="*60)
    
    # 1. 加载数据
    print("\n步骤1: 加载数据")
    
    # 尝试加载真实数据
    data_files = [
        'data/btc_bars_60min.csv',
        'results/btc_bars_60min.csv',
        'bars_60min.csv'
    ]
    
    bars = None
    for file_path in data_files:
        try:
            bars = pd.read_csv(file_path, index_col=0, parse_dates=True)
            print(f"  ✓ 成功加载数据: {file_path}")
            break
        except:
            continue
    
    # 如果没有真实数据，生成模拟数据
    if bars is None:
        print("  ! 未找到真实数据，生成模拟数据...")
        np.random.seed(42)
        n_bars = 10000
        dates = pd.date_range('2020-01-01', periods=n_bars, freq='60min')
        
        # 生成随机游走价格
        returns = np.random.normal(0.0001, 0.01, n_bars)
        prices = 40000 * np.exp(np.cumsum(returns))
        
        bars = pd.DataFrame({
            'close': prices,
            'high': prices * (1 + np.abs(np.random.normal(0, 0.005, n_bars))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.005, n_bars))),
            'open': prices * (1 + np.random.normal(0, 0.002, n_bars))
        }, index=dates)
    
    print(f"  - 数据起始: {bars.index[0]}")
    print(f"  - 数据结束: {bars.index[-1]}")
    print(f"  - Bar数量: {len(bars)}")
    print(f"  - 列: {list(bars.columns)}")
    
    # 2. 拟合ManipScore模型
    print("\n步骤2: 拟合ManipScore模型")
    config = StrategyConfig()
    bars, model = fit_manipscore_model(bars, config.L_past, config.vol_window)
    
    # 3. 生成信号
    print("\n步骤3: 生成交易信号")
    signals = generate_asymmetric_signals(bars, config)
    
    # 4. 运行回测
    print("\n步骤4: 运行回测")
    result = run_backtest(bars, signals, config, initial_capital=10000)
    
    # 5. 输出结果
    print("\n" + "="*60)
    print("回测结果")
    print("="*60)
    stats = result['stats']
    print(f"总收益:       {stats['total_return']*100:>10.2f}%")
    print(f"年化收益:     {stats['ann_return']*100:>10.2f}%")
    print(f"Sharpe比率:   {stats['sharpe_ratio']:>10.2f}")
    print(f"最大回撤:     {stats['max_drawdown']*100:>10.2f}%")
    print(f"交易次数:     {stats['num_trades']:>10}")
    print(f"胜率:         {stats['win_rate']*100:>10.1f}%")
    print(f"平均盈利:     {stats['avg_win']*100:>10.2f}%")
    print(f"平均亏损:     {stats['avg_loss']*100:>10.2f}%")
    print(f"利润因子:     {stats['profit_factor']:>10.2f}")
    print(f"最终权益:     ${stats['final_equity']:>10,.2f}")
    print("="*60)
    
    # 6. 显示前10笔交易
    if len(result['trades']) > 0:
        print("\n前10笔交易:")
        print("-"*100)
        print(f"{'入场时间':<20} {'入场价':<12} {'出场时间':<20} {'出场价':<12} {'原因':<6} {'收益%':<10}")
        print("-"*100)
        for i, trade in enumerate(result['trades'][:10]):
            print(f"{str(trade.entry_time):<20} {trade.entry_price:<12.2f} "
                  f"{str(trade.exit_time):<20} {trade.exit_price:<12.2f} "
                  f"{trade.exit_reason:<6} {trade.pnl_pct*100:<10.2f}")
        print("-"*100)
    
    print("\n✓ 回测完成！")


if __name__ == "__main__":
    main()

