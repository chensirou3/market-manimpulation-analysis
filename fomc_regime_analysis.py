"""
FOMC事件窗口分析

测试策略在FOMC事件窗口内外的表现差异

数据要求:
- FOMC事件CSV: data/fomc_events_2015_2023.csv
- Bar数据: results/bars_{timeframe}_{symbol}_full_with_manipscore.csv

输出:
- results/fomc_regime_summary_all.csv: 所有symbol/timeframe/regime的汇总结果
- results/fomc_regime_detailed_{symbol}_{timeframe}.csv: 详细的逐笔交易记录
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import pytz
from typing import Dict, List, Tuple

# Import existing strategy modules
import sys
sys.path.append('market-manimpulation-analysis')

from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.backtest_reversal import run_extreme_reversal_backtest
from src.strategies.trend_features import compute_trend_strength, compute_extreme_trend_thresholds


# ==================== 信号生成函数 ====================

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

    # 计算极端阈值
    thresholds = compute_extreme_trend_thresholds(bars, quantile=config.q_extreme_trend)
    threshold = thresholds['threshold']

    # 识别极端趋势
    extreme_up = bars['TS'] > threshold
    extreme_down = bars['TS'] < -threshold

    # 识别高操纵
    manip_threshold = bars['ManipScore'].quantile(config.q_manip)
    high_manip = bars['ManipScore'] > manip_threshold

    # 生成信号
    signals = pd.DataFrame(index=bars.index)
    signals['signal'] = 0
    signals.loc[extreme_up & high_manip, 'signal'] = 1
    signals.loc[extreme_down & high_manip, 'signal'] = 1

    # 延迟信号避免前视偏差
    signals['signal'] = signals['signal'].shift(1).fillna(0)

    return signals


# ==================== FOMC事件数据加载 ====================

def load_fomc_events(csv_path: str = 'market-manimpulation-analysis/data/fomc_events_2015_2023.csv') -> pd.DataFrame:
    """
    加载FOMC事件数据并转换为UTC时间
    
    Returns:
        DataFrame with columns: event_id, release_datetime_utc (datetime64[ns, UTC])
    """
    print(f"Loading FOMC events from {csv_path}...")
    
    df = pd.read_csv(csv_path)
    
    # 转换UTC时间列为datetime
    df['release_datetime_utc'] = pd.to_datetime(df['release_datetime_utc'], utc=True)
    
    # 只保留需要的列
    fomc_df = df[['event_id', 'release_datetime_utc', 'event_name']].copy()
    
    print(f"  Loaded {len(fomc_df)} FOMC events")
    print(f"  Date range: {fomc_df['release_datetime_utc'].min()} to {fomc_df['release_datetime_utc'].max()}")
    
    return fomc_df


# ==================== Bar数据标记FOMC窗口 ====================

def tag_fomc_windows_for_bars(
    bars: pd.DataFrame,
    fomc_df: pd.DataFrame,
    bar_size: str,
    hours_before: int = 8,
    hours_after: int = 8
) -> pd.DataFrame:
    """
    为bar数据添加is_fomc_window列
    
    Args:
        bars: Bar数据，必须有timestamp列
        fomc_df: FOMC事件数据
        bar_size: 时间周期 ('5min', '15min', '30min', '60min', '4h', '1d')
        hours_before: FOMC事件前多少小时算作窗口
        hours_after: FOMC事件后多少小时算作窗口
    
    Returns:
        bars with 'is_fomc_window' column (0/1)
    """
    bars = bars.copy()
    
    # 确保timestamp是datetime类型且有时区信息
    if 'timestamp' not in bars.columns:
        raise ValueError("bars must have 'timestamp' column")
    
    bars['timestamp'] = pd.to_datetime(bars['timestamp'], utc=True)
    
    # 初始化is_fomc_window列
    bars['is_fomc_window'] = 0
    
    # 对于日线数据，使用日期匹配
    if bar_size == '1d':
        # 提取日期
        bars['date'] = bars['timestamp'].dt.date
        fomc_dates = fomc_df['release_datetime_utc'].dt.date.unique()
        
        # 标记FOMC日期（可选：±1天）
        bars.loc[bars['date'].isin(fomc_dates), 'is_fomc_window'] = 1
        
        bars.drop('date', axis=1, inplace=True)
        
    else:
        # 对于日内数据，使用时间窗口
        for _, event in fomc_df.iterrows():
            release_time = event['release_datetime_utc']
            
            # 定义窗口
            window_start = release_time - timedelta(hours=hours_before)
            window_end = release_time + timedelta(hours=hours_after)
            
            # 标记在窗口内的bar
            mask = (bars['timestamp'] >= window_start) & (bars['timestamp'] <= window_end)
            bars.loc[mask, 'is_fomc_window'] = 1
    
    fomc_count = bars['is_fomc_window'].sum()
    total_count = len(bars)
    fomc_pct = fomc_count / total_count * 100 if total_count > 0 else 0
    
    print(f"  Tagged {fomc_count}/{total_count} bars ({fomc_pct:.2f}%) as FOMC window")
    
    return bars


# ==================== 加载Bar数据 ====================

def load_bars_for_symbol_timeframe(
    symbol: str,
    timeframe: str,
    results_dir: str = 'market-manimpulation-analysis/results'
) -> pd.DataFrame:
    """
    加载指定symbol和timeframe的bar数据
    
    Args:
        symbol: 'btc', 'eth', 'xauusd'
        timeframe: '5min', '15min', '30min', '60min', '4h', '1d'
        results_dir: results目录路径
    
    Returns:
        DataFrame with bars data
    """
    # 构建文件名
    if symbol.lower() in ['btc', 'eth']:
        filename = f'bars_{timeframe}_{symbol.lower()}_full_with_manipscore.csv'
    else:  # xauusd
        filename = f'bars_{timeframe}_with_manipscore_full.csv'
    
    filepath = Path(results_dir) / filename
    
    if not filepath.exists():
        raise FileNotFoundError(f"Bar data not found: {filepath}")
    
    print(f"Loading {symbol} {timeframe} bars from {filepath}...")
    bars = pd.read_csv(filepath)
    
    # 确保timestamp是datetime类型
    bars['timestamp'] = pd.to_datetime(bars['timestamp'], utc=True)
    
    print(f"  Loaded {len(bars)} bars")
    print(f"  Date range: {bars['timestamp'].min()} to {bars['timestamp'].max()}")

    return bars


# ==================== 回测函数 ====================

def run_backtest_for_regime(
    bars: pd.DataFrame,
    config: ExtremeReversalConfig,
    regime: str = 'all'
):
    """
    对指定regime的bars运行回测

    Args:
        bars: Bar数据（已包含is_fomc_window列）
        config: 策略配置
        regime: 'all', 'fomc_window', 'non_fomc'

    Returns:
        BacktestResult object
    """
    # 根据regime筛选bars
    if regime == 'fomc_window':
        bars_subset = bars[bars['is_fomc_window'] == 1].copy()
    elif regime == 'non_fomc':
        bars_subset = bars[bars['is_fomc_window'] == 0].copy()
    else:  # 'all'
        bars_subset = bars.copy()

    if len(bars_subset) == 0:
        print(f"    WARNING: No bars for regime '{regime}'")
        return None

    print(f"    Running backtest for regime '{regime}' ({len(bars_subset)} bars)...")

    # 计算趋势强度（如果还没有）
    if 'TS' not in bars_subset.columns:
        bars_subset = compute_trend_strength(
            bars_subset,
            L_past=config.L_past,
            vol_window=config.vol_window
        )

    # 生成信号
    signals = generate_asymmetric_signals(bars_subset, config)

    # 添加信号到bars
    bars_subset['exec_signal'] = signals['signal']

    # 调试：打印信号统计
    signal_count = (bars_subset['exec_signal'] != 0).sum()
    print(f"      Generated {signal_count} signals ({signal_count/len(bars_subset)*100:.2f}%)")

    # 运行回测
    result = run_extreme_reversal_backtest(
        bars_subset,
        bars_subset['exec_signal'],
        config,
        initial_capital=10000
    )

    return result


def calculate_performance_metrics(result, bars_count: int, years: float) -> Dict:
    """
    从回测结果计算性能指标

    Args:
        result: run_extreme_reversal_backtest的返回结果 (BacktestResult对象)
        bars_count: bar数量
        years: 时间跨度（年）

    Returns:
        Dict with performance metrics
    """
    if result is None:
        return {
            'total_return': np.nan,
            'ann_return': np.nan,
            'ann_vol': np.nan,
            'sharpe': np.nan,
            'max_dd': np.nan,
            'num_trades': 0,
            'win_rate': np.nan,
            'avg_pnl': np.nan,
            'avg_holding_time': np.nan
        }

    # BacktestResult是一个dataclass，有stats字典
    stats = result.stats if hasattr(result, 'stats') else {}

    # 提取基本指标（注意键名）
    total_return = stats.get('total_return', 0)  # 不是total_return_pct
    sharpe = stats.get('sharpe_ratio', 0)
    max_dd = stats.get('max_drawdown', 0)  # 不是max_drawdown_pct
    num_trades = stats.get('n_trades', 0)  # 不是num_trades
    win_rate = stats.get('win_rate', 0)

    # 计算年化收益
    if years > 0:
        ann_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100
    else:
        ann_return = 0

    # 计算年化波动率（从Sharpe反推）
    if sharpe != 0 and ann_return != 0:
        ann_vol = ann_return / sharpe
    else:
        ann_vol = 0

    # 平均PnL
    if hasattr(result, 'trades') and len(result.trades) > 0:
        # trades是Trade对象列表
        trades_data = []
        for trade in result.trades:
            trades_data.append({
                'pnl_pct': trade.pnl_pct if hasattr(trade, 'pnl_pct') else 0,
                'holding_time': trade.exit_bar - trade.entry_bar if hasattr(trade, 'exit_bar') and hasattr(trade, 'entry_bar') else 0
            })

        if trades_data:
            trades_df = pd.DataFrame(trades_data)
            avg_pnl = trades_df['pnl_pct'].mean()
            avg_holding_time = trades_df['holding_time'].mean()
        else:
            avg_pnl = 0
            avg_holding_time = np.nan
    else:
        avg_pnl = 0
        avg_holding_time = np.nan

    return {
        'total_return': total_return,
        'ann_return': ann_return,
        'ann_vol': ann_vol,
        'sharpe': sharpe,
        'max_dd': max_dd,
        'num_trades': num_trades,
        'win_rate': win_rate * 100,  # 转换为百分比
        'avg_pnl': avg_pnl,
        'avg_holding_time': avg_holding_time
    }


# ==================== 主分析函数 ====================

def analyze_fomc_regime_for_symbol_timeframe(
    symbol: str,
    timeframe: str,
    fomc_df: pd.DataFrame,
    config: ExtremeReversalConfig,
    hours_before: int = 8,
    hours_after: int = 8
) -> pd.DataFrame:
    """
    分析单个symbol和timeframe在FOMC窗口内外的表现

    Returns:
        DataFrame with results for all regimes
    """
    print(f"\n{'='*80}")
    print(f"Analyzing {symbol.upper()} {timeframe}")
    print(f"{'='*80}")

    # 1. 加载bars
    try:
        bars = load_bars_for_symbol_timeframe(symbol, timeframe)
    except FileNotFoundError as e:
        print(f"  SKIP: {e}")
        return pd.DataFrame()

    # 2. 标记FOMC窗口
    bars = tag_fomc_windows_for_bars(
        bars, fomc_df, timeframe,
        hours_before=hours_before,
        hours_after=hours_after
    )

    # 3. 计算时间跨度
    time_span = (bars['timestamp'].max() - bars['timestamp'].min()).days / 365.25

    # 4. 对三种regime运行回测
    regimes = ['all', 'fomc_window', 'non_fomc']
    results_list = []

    for regime in regimes:
        print(f"\n  Regime: {regime}")

        # 运行回测
        result = run_backtest_for_regime(bars, config, regime)

        # 计算性能指标
        if regime == 'fomc_window':
            regime_bars = bars[bars['is_fomc_window'] == 1]
        elif regime == 'non_fomc':
            regime_bars = bars[bars['is_fomc_window'] == 0]
        else:
            regime_bars = bars

        regime_time_span = (regime_bars['timestamp'].max() - regime_bars['timestamp'].min()).days / 365.25

        metrics = calculate_performance_metrics(result, len(regime_bars), regime_time_span)

        # 添加元数据
        metrics['symbol'] = symbol.upper()
        metrics['timeframe'] = timeframe
        metrics['regime'] = regime
        metrics['bars_count'] = len(regime_bars)
        metrics['time_span_years'] = regime_time_span

        results_list.append(metrics)

        # 打印结果
        print(f"    Total Return: {metrics['total_return']:.2f}%")
        print(f"    Ann Return: {metrics['ann_return']:.2f}%")
        print(f"    Sharpe: {metrics['sharpe']:.2f}")
        print(f"    Max DD: {metrics['max_dd']:.2f}%")
        print(f"    Trades: {metrics['num_trades']}")
        print(f"    Win Rate: {metrics['win_rate']:.2f}%")

    return pd.DataFrame(results_list)


# ==================== 批量分析 ====================

def run_full_fomc_analysis(
    symbols: List[str] = ['btc', 'eth', 'xauusd'],
    timeframes: List[str] = ['5min', '15min', '30min', '60min', '4h', '1d'],
    cost_per_trade: float = 0.0007,  # 7bp
    hours_before: int = 8,
    hours_after: int = 8,
    output_dir: str = 'market-manimpulation-analysis/results'
) -> pd.DataFrame:
    """
    对所有symbol和timeframe运行FOMC regime分析

    Args:
        symbols: 要分析的symbol列表
        timeframes: 要分析的timeframe列表
        cost_per_trade: 每笔交易成本
        hours_before: FOMC事件前窗口（小时）
        hours_after: FOMC事件后窗口（小时）
        output_dir: 输出目录

    Returns:
        DataFrame with all results
    """
    print("="*80)
    print("FOMC REGIME ANALYSIS")
    print("="*80)
    print(f"Symbols: {symbols}")
    print(f"Timeframes: {timeframes}")
    print(f"FOMC window: -{hours_before}h to +{hours_after}h")
    print(f"Cost per trade: {cost_per_trade*100:.2f}%")
    print("="*80)

    # 1. 加载FOMC事件
    fomc_df = load_fomc_events()

    # 2. 对每个symbol和timeframe运行分析
    all_results = []

    for symbol in symbols:
        for timeframe in timeframes:
            # 创建配置
            config = ExtremeReversalConfig(
                bar_size=timeframe,
                L_past=5,
                vol_window=20,
                q_extreme_trend=0.9,
                q_manip=0.9,
                holding_horizon=5,
                atr_window=10,
                sl_atr_mult=0.5,
                tp_atr_mult=0.8,
                cost_per_trade=cost_per_trade
            )

            try:
                # 运行分析
                results_df = analyze_fomc_regime_for_symbol_timeframe(
                    symbol, timeframe, fomc_df, config,
                    hours_before=hours_before,
                    hours_after=hours_after
                )

                if not results_df.empty:
                    all_results.append(results_df)

            except Exception as e:
                print(f"\n  ERROR analyzing {symbol} {timeframe}: {e}")
                import traceback
                traceback.print_exc()
                continue

    # 3. 合并所有结果
    if all_results:
        summary_df = pd.concat(all_results, ignore_index=True)

        # 保存结果
        output_path = Path(output_dir) / 'fomc_regime_summary_all.csv'
        summary_df.to_csv(output_path, index=False)
        print(f"\n{'='*80}")
        print(f"Results saved to: {output_path}")
        print(f"{'='*80}")

        return summary_df
    else:
        print("\nNo results generated!")
        return pd.DataFrame()


# ==================== 结果分析和可视化 ====================

def generate_fomc_comparison_report(summary_df: pd.DataFrame, output_dir: str = 'market-manimpulation-analysis/results'):
    """
    生成FOMC对比报告
    """
    if summary_df.empty:
        print("No data to generate report")
        return

    print("\n" + "="*80)
    print("FOMC REGIME COMPARISON REPORT")
    print("="*80)

    # 按symbol和timeframe分组
    for symbol in summary_df['symbol'].unique():
        print(f"\n{'='*80}")
        print(f"{symbol}")
        print(f"{'='*80}")

        symbol_data = summary_df[summary_df['symbol'] == symbol]

        for timeframe in symbol_data['timeframe'].unique():
            tf_data = symbol_data[symbol_data['timeframe'] == timeframe]

            print(f"\n{timeframe}:")
            print("-" * 80)

            # 创建对比表
            comparison = tf_data.pivot_table(
                index='regime',
                values=['total_return', 'ann_return', 'sharpe', 'max_dd', 'num_trades', 'win_rate'],
                aggfunc='first'
            )

            print(comparison.to_string())

            # 计算FOMC vs Non-FOMC的差异
            if 'fomc_window' in tf_data['regime'].values and 'non_fomc' in tf_data['regime'].values:
                fomc_row = tf_data[tf_data['regime'] == 'fomc_window'].iloc[0]
                non_fomc_row = tf_data[tf_data['regime'] == 'non_fomc'].iloc[0]

                print(f"\nFOMC vs Non-FOMC Difference:")
                print(f"  Return: {fomc_row['total_return'] - non_fomc_row['total_return']:+.2f}%")
                print(f"  Sharpe: {fomc_row['sharpe'] - non_fomc_row['sharpe']:+.2f}")
                print(f"  Trades: {fomc_row['num_trades'] - non_fomc_row['num_trades']:+.0f}")
                print(f"  Win Rate: {fomc_row['win_rate'] - non_fomc_row['win_rate']:+.2f}%")


# ==================== 主程序 ====================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='FOMC Regime Analysis')
    parser.add_argument('--symbols', nargs='+', default=['btc', 'eth', 'xauusd'],
                       help='Symbols to analyze')
    parser.add_argument('--timeframes', nargs='+', default=['5min', '15min', '30min', '60min', '4h', '1d'],
                       help='Timeframes to analyze')
    parser.add_argument('--cost', type=float, default=0.0007,
                       help='Cost per trade (default: 0.0007 = 7bp)')
    parser.add_argument('--hours-before', type=int, default=8,
                       help='Hours before FOMC event (default: 8)')
    parser.add_argument('--hours-after', type=int, default=8,
                       help='Hours after FOMC event (default: 8)')

    args = parser.parse_args()

    # 运行分析
    summary_df = run_full_fomc_analysis(
        symbols=args.symbols,
        timeframes=args.timeframes,
        cost_per_trade=args.cost,
        hours_before=args.hours_before,
        hours_after=args.hours_after
    )

    # 生成报告
    if not summary_df.empty:
        generate_fomc_comparison_report(summary_df)



