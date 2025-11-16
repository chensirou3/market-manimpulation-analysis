"""
BTC Bear Market Analysis (2021-2023)
分析BTC在2021-2023年熊市期间的策略表现
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.append('market-manimpulation-analysis')

from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.backtest_reversal import run_extreme_reversal_backtest
from src.strategies.trend_features import (
    compute_trend_strength,
    compute_extreme_trend_thresholds
)


def analyze_bear_market_period(symbol: str = 'btc', start_date: str = '2021-01-01', end_date: str = '2023-12-31'):
    """
    分析熊市期间的策略表现
    
    BTC价格走势:
    - 2021年初: ~$30,000
    - 2021年11月: ~$69,000 (历史最高点)
    - 2022年底: ~$16,000 (熊市底部)
    - 2023年底: ~$42,000 (复苏)
    
    整体趋势: 2021年11月到2022年底是明显的熊市
    """
    
    results_dir = Path(__file__).parent / 'results'
    
    # 测试所有时间周期
    timeframes = ['5min', '15min', '30min', '60min', '4h', '1d']
    
    all_results = []
    
    for timeframe in timeframes:
        print(f"\n{'='*60}")
        print(f"分析 {symbol.upper()} {timeframe} 在熊市期间 ({start_date} to {end_date})")
        print(f"{'='*60}")
        
        # 加载数据
        data_file = results_dir / f'bars_{timeframe}_{symbol}_full_with_manipscore.csv'
        
        if not data_file.exists():
            print(f"⚠️  数据文件不存在: {data_file}")
            continue
        
        df = pd.read_csv(data_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 筛选熊市期间数据
        mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
        df_bear = df[mask].copy()
        
        if len(df_bear) == 0:
            print(f"⚠️  熊市期间无数据")
            continue
        
        # 计算市场表现
        market_return = (df_bear['close'].iloc[-1] / df_bear['close'].iloc[0] - 1) * 100
        
        print(f"\n📊 市场表现:")
        print(f"  起始价格: ${df_bear['close'].iloc[0]:,.2f}")
        print(f"  结束价格: ${df_bear['close'].iloc[-1]:,.2f}")
        print(f"  市场收益: {market_return:+.2f}%")
        print(f"  数据点数: {len(df_bear):,}")
        
        # 创建配置
        config = ExtremeReversalConfig(
            L_past=5,
            vol_window=20,
            q_extreme_trend=0.9,
            q_manip=0.9,
            holding_horizon=5,
            atr_window=10,
            sl_atr_mult=0.5,
            tp_atr_mult=0.8,
            cost_per_trade=0.0007  # 7bp
        )

        # 计算趋势强度
        if 'TS' not in df_bear.columns:
            df_bear = compute_trend_strength(df_bear, config.L_past, config.vol_window)

        # 计算阈值
        thresholds = compute_extreme_trend_thresholds(df_bear, quantile=config.q_extreme_trend)
        T_trend = thresholds['threshold']
        M_thresh = df_bear['ManipScore'].quantile(config.q_manip)

        # 生成信号
        extreme_up = (
            (df_bear['TS'] > T_trend) &
            (df_bear['returns'] > 0) &
            (df_bear['ManipScore'] > M_thresh)
        )

        extreme_down = (
            (df_bear['TS'] < -T_trend) &
            (df_bear['returns'] < 0) &
            (df_bear['ManipScore'] > M_thresh)
        )

        signal_raw = pd.Series(0, index=df_bear.index)
        signal_raw[extreme_up] = -1  # Short on extreme up
        signal_raw[extreme_down] = +1  # Long on extreme down
        signal_exec = signal_raw.shift(1).fillna(0)

        # 测试三种策略
        strategies = {
            'long_only': signal_exec.copy(),
            'symmetric': signal_exec.copy(),
            'short_only': signal_exec.copy()
        }

        # 修改信号
        strategies['long_only'][strategies['long_only'] == -1] = 0  # Remove shorts
        strategies['short_only'][strategies['short_only'] == 1] = 0  # Remove longs

        for strategy_name, signals in strategies.items():
            print(f"\n--- {strategy_name.upper()} 策略 ---")

            # 运行回测
            result = run_extreme_reversal_backtest(
                bars=df_bear,
                exec_signals=signals,
                config=config,
                initial_capital=10000.0
            )

            stats = result.stats

            # 保存结果
            result_data = {
                'period': f'{start_date}_to_{end_date}',
                'timeframe': timeframe,
                'strategy': strategy_name,
                'market_return': market_return,
                'total_return': stats.get('total_return', 0) * 100,  # Convert to percentage
                'sharpe_ratio': stats.get('sharpe_ratio', 0),
                'win_rate': stats.get('win_rate', 0) * 100,  # Convert to percentage
                'n_trades': stats.get('n_trades', 0),
                'avg_winner': stats.get('avg_winner', 0),
                'avg_loser': stats.get('avg_loser', 0),
                'profit_factor': stats.get('profit_factor', 0),
                'max_drawdown': stats.get('max_drawdown', 0) * 100,  # Convert to percentage
                'annualized_return': stats.get('annualized_return', 0) * 100,
                'start_price': df_bear['close'].iloc[0],
                'end_price': df_bear['close'].iloc[-1],
                'n_bars': len(df_bear)
            }

            all_results.append(result_data)

            # 打印结果
            print(f"  总收益: {stats.get('total_return', 0)*100:+.2f}%")
            print(f"  年化收益: {stats.get('annualized_return', 0)*100:+.2f}%")
            print(f"  Sharpe: {stats.get('sharpe_ratio', 0):.2f}")
            print(f"  胜率: {stats.get('win_rate', 0)*100:.1f}%")
            print(f"  交易次数: {stats.get('n_trades', 0)}")
            print(f"  平均盈利: {stats.get('avg_winner', 0):.2f}")
            print(f"  平均亏损: {stats.get('avg_loser', 0):.2f}")
            print(f"  盈亏比: {stats.get('profit_factor', 0):.2f}")
            print(f"  最大回撤: {stats.get('max_drawdown', 0)*100:.2f}%")
    
    # 保存结果
    results_df = pd.DataFrame(all_results)
    output_file = results_dir / f'{symbol}_bear_market_2021_2023_analysis.csv'
    results_df.to_csv(output_file, index=False)
    print(f"\n✅ 结果已保存到: {output_file}")
    
    # 打印总结
    print(f"\n{'='*60}")
    print("📊 熊市期间策略表现总结")
    print(f"{'='*60}")
    
    # 按策略类型汇总
    for strategy in ['long_only', 'symmetric', 'short_only']:
        strategy_results = results_df[results_df['strategy'] == strategy]
        
        print(f"\n{strategy.upper()} 策略:")
        print(f"  平均收益: {strategy_results['total_return'].mean():+.2f}%")
        print(f"  平均Sharpe: {strategy_results['sharpe_ratio'].mean():.2f}")
        print(f"  平均胜率: {strategy_results['win_rate'].mean():.1f}%")
        print(f"  总交易次数: {strategy_results['n_trades'].sum()}")
        
        # 找出最佳时间周期
        best_idx = strategy_results['sharpe_ratio'].idxmax()
        if pd.notna(best_idx):
            best = strategy_results.loc[best_idx]
            print(f"  最佳时间周期: {best['timeframe']} (Sharpe {best['sharpe_ratio']:.2f})")
    
    # 对比市场表现
    print(f"\n市场收益 vs 策略收益:")
    print(f"  市场收益: {results_df['market_return'].iloc[0]:+.2f}%")
    print(f"  Long-Only平均: {results_df[results_df['strategy']=='long_only']['total_return'].mean():+.2f}%")
    print(f"  Short-Only平均: {results_df[results_df['strategy']=='short_only']['total_return'].mean():+.2f}%")
    print(f"  Symmetric平均: {results_df[results_df['strategy']=='symmetric']['total_return'].mean():+.2f}%")
    
    return results_df


if __name__ == '__main__':
    # 分析BTC 2021-2023熊市期间
    results = analyze_bear_market_period(
        symbol='btc',
        start_date='2021-01-01',
        end_date='2023-12-31'
    )
    
    print("\n✅ 熊市分析完成！")

