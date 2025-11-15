"""
全数据回测 - 极端反转策略
Full Data Backtest - Extreme Reversal Strategy

对2015-2025年全部数据进行回测分析
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime

from src.strategies import (
    ExtremeReversalConfig,
    generate_extreme_reversal_signals,
    run_extreme_reversal_backtest,
    print_backtest_summary
)

from src.visualization import (
    plot_equity_curve,
    plot_conditional_returns,
    plot_signal_diagnostics,
    plot_comprehensive_analysis
)


def load_all_data():
    """加载所有已处理的数据"""
    results_dir = Path('results')
    all_files = sorted(results_dir.glob('bars_with_manipscore_*.csv'))
    
    print(f"📁 找到 {len(all_files)} 个数据文件")
    print("正在加载...")
    
    dfs = []
    for i, file in enumerate(all_files, 1):
        if i % 10 == 0:
            print(f"  进度: {i}/{len(all_files)}")
        
        df = pd.read_csv(file, index_col=0, parse_dates=True)
        dfs.append(df)
    
    bars = pd.concat(dfs, axis=0)
    bars = bars.sort_index()
    
    # 确保有returns列
    if 'returns' not in bars.columns and 'close' in bars.columns:
        bars['returns'] = bars['close'].pct_change()
    
    print(f"✅ 加载完成！")
    print(f"   总K线数: {len(bars):,}")
    print(f"   时间范围: {bars.index[0]} 到 {bars.index[-1]}")
    print(f"   数据大小: {bars.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
    return bars


def run_yearly_backtest(bars, config):
    """按年份分别回测"""
    
    print("\n" + "=" * 80)
    print("按年份回测分析")
    print("=" * 80)
    
    # 提取年份
    bars['year'] = bars.index.year
    years = sorted(bars['year'].unique())
    
    yearly_results = []
    
    for year in years:
        print(f"\n{'='*80}")
        print(f"回测 {year} 年")
        print(f"{'='*80}")
        
        # 筛选该年数据
        year_bars = bars[bars['year'] == year].copy()
        
        print(f"数据量: {len(year_bars):,} 根K线")
        
        # 生成信号
        year_bars_with_signals = generate_extreme_reversal_signals(year_bars, config)
        
        n_signals = (year_bars_with_signals['exec_signal'] != 0).sum()
        n_long = (year_bars_with_signals['exec_signal'] == 1).sum()
        n_short = (year_bars_with_signals['exec_signal'] == -1).sum()
        
        print(f"信号数: {n_signals} (做多: {n_long}, 做空: {n_short})")
        
        if n_signals == 0:
            print("⚠️ 无信号，跳过")
            continue
        
        # 运行回测
        result = run_extreme_reversal_backtest(
            year_bars_with_signals,
            year_bars_with_signals['exec_signal'],
            config,
            initial_capital=10000.0
        )
        
        # 保存结果
        yearly_results.append({
            'year': year,
            'n_bars': len(year_bars),
            'n_signals': n_signals,
            'n_long': n_long,
            'n_short': n_short,
            'signal_rate': n_signals / len(year_bars) * 100,
            'n_trades': result.stats.get('n_trades', 0),
            'total_return': result.stats.get('total_return', 0),
            'sharpe_ratio': result.stats.get('sharpe_ratio', 0),
            'max_drawdown': result.stats.get('max_drawdown', 0),
            'win_rate': result.stats.get('win_rate', 0),
            'profit_factor': result.stats.get('profit_factor', 0),
            'avg_bars_held': result.stats.get('avg_bars_held', 0),
        })
        
        # 打印简要结果
        print(f"\n结果:")
        print(f"  总收益: {result.stats.get('total_return', 0):>8.2%}")
        print(f"  Sharpe: {result.stats.get('sharpe_ratio', 0):>8.2f}")
        print(f"  胜率:   {result.stats.get('win_rate', 0):>8.2%}")
        print(f"  交易数: {result.stats.get('n_trades', 0):>8}")
    
    return pd.DataFrame(yearly_results)


def main():
    """主函数"""
    
    print("=" * 80)
    print("极端反转策略 - 全数据回测 (2015-2025)")
    print("Extreme Reversal Strategy - Full Data Backtest")
    print("=" * 80)
    print()
    
    # 步骤1: 加载全部数据
    print("【步骤 1】加载全部数据")
    print("-" * 80)
    bars = load_all_data()
    print()
    
    # 步骤2: 配置策略
    print("【步骤 2】配置策略")
    print("-" * 80)
    
    config = ExtremeReversalConfig(
        L_past=5,
        vol_window=20,
        q_extreme_trend=0.90,
        use_normalized_trend=True,
        min_abs_R_past=0.005,
        q_manip=0.90,
        min_manip_score=0.7,
        holding_horizon=5,
        atr_window=10,
        sl_atr_mult=0.5,
        tp_atr_mult=0.8,
        cost_per_trade=0.0001
    )
    
    print(f"  趋势回看: {config.L_past} 根K线")
    print(f"  极端趋势阈值: {config.q_extreme_trend} 分位数")
    print(f"  高ManipScore阈值: {config.q_manip} 分位数")
    print(f"  最大持仓: {config.holding_horizon} 根K线")
    print()
    
    # 步骤3: 全数据回测
    print("【步骤 3】全数据回测")
    print("-" * 80)
    
    start_time = datetime.now()
    
    # 生成信号
    print("生成信号...")
    bars_with_signals = generate_extreme_reversal_signals(bars, config)
    
    n_signals = (bars_with_signals['exec_signal'] != 0).sum()
    n_long = (bars_with_signals['exec_signal'] == 1).sum()
    n_short = (bars_with_signals['exec_signal'] == -1).sum()
    
    print(f"✅ 信号生成完成")
    print(f"   总信号数: {n_signals:,}")
    print(f"   做多信号: {n_long:,}")
    print(f"   做空信号: {n_short:,}")
    print(f"   信号率: {n_signals / len(bars_with_signals) * 100:.3f}%")
    print()
    
    # 运行回测
    print("运行回测...")
    result = run_extreme_reversal_backtest(
        bars_with_signals,
        bars_with_signals['exec_signal'],
        config,
        initial_capital=10000.0
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"✅ 回测完成 (耗时: {elapsed:.1f}秒)")
    print()
    
    # 打印结果
    print_backtest_summary(result)
    
    # 步骤4: 按年份分析
    yearly_df = run_yearly_backtest(bars, config)
    
    # 保存年度结果
    yearly_df.to_csv('results/extreme_reversal_yearly_results.csv', 
                     index=False, encoding='utf-8-sig')
    print(f"\n✅ 年度结果已保存: results/extreme_reversal_yearly_results.csv")
    
    # 打印年度汇总
    print("\n" + "=" * 80)
    print("年度结果汇总")
    print("=" * 80)
    print()
    print(yearly_df.to_string(index=False))
    
    # 步骤5: 生成图表
    print("\n\n【步骤 4】生成图表")
    print("-" * 80)
    
    # 权益曲线
    fig1 = plot_equity_curve(result.equity_curve, 
                             title="Extreme Reversal Strategy - Full Data (2015-2025)",
                             show_drawdown=True)
    plt.savefig('results/extreme_reversal_full_data_equity.png', dpi=150, bbox_inches='tight')
    print("  ✅ 权益曲线: results/extreme_reversal_full_data_equity.png")
    
    # 条件收益
    fig2 = plot_conditional_returns(bars_with_signals, holding_horizon=config.holding_horizon)
    plt.savefig('results/extreme_reversal_full_data_returns.png', dpi=150, bbox_inches='tight')
    print("  ✅ 条件收益: results/extreme_reversal_full_data_returns.png")
    
    # 信号诊断
    fig3 = plot_signal_diagnostics(bars_with_signals)
    plt.savefig('results/extreme_reversal_full_data_diagnostics.png', dpi=150, bbox_inches='tight')
    print("  ✅ 信号诊断: results/extreme_reversal_full_data_diagnostics.png")
    
    # 综合分析
    fig4 = plot_comprehensive_analysis(bars_with_signals, result.equity_curve, result.trades)
    plt.savefig('results/extreme_reversal_full_data_comprehensive.png', dpi=150, bbox_inches='tight')
    print("  ✅ 综合分析: results/extreme_reversal_full_data_comprehensive.png")
    
    print()
    print("=" * 80)
    print("🎉 全数据回测完成！")
    print("=" * 80)
    
    # 显示图表
    plt.show()


if __name__ == "__main__":
    main()

