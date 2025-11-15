"""
自动运行参数优化（无交互）
Auto-run parameter optimization (non-interactive)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime
import multiprocessing

from parameter_optimization import (
    optimize_parameters,
    analyze_optimization_results,
    visualize_optimization_results,
    PARAM_GRID
)


def load_all_data():
    """加载所有数据"""
    print("=" * 80)
    print("加载数据")
    print("=" * 80)
    print()
    
    results_dir = Path('results')
    all_files = sorted(results_dir.glob('bars_with_manipscore_*.csv'))
    
    print(f"找到 {len(all_files)} 个数据文件")
    
    dfs = []
    for i, file in enumerate(all_files, 1):
        if i % 10 == 0:
            print(f"  加载进度: {i}/{len(all_files)}")
        df = pd.read_csv(file, index_col=0, parse_dates=True)
        dfs.append(df)
    
    bars = pd.concat(dfs, axis=0)
    bars = bars.sort_index()
    
    if 'returns' not in bars.columns and 'close' in bars.columns:
        bars['returns'] = bars['close'].pct_change()
    
    print(f"✅ 数据加载完成")
    print(f"   总K线数: {len(bars):,}")
    print(f"   时间范围: {bars.index[0]} 到 {bars.index[-1]}")
    print()
    
    return bars


def main():
    """主函数"""
    
    print("=" * 80)
    print("极端反转策略 - 参数优化系统 (自动模式)")
    print("Parameter Optimization System (Auto Mode)")
    print("=" * 80)
    print()
    
    # 配置
    sampling_method = 'lhs'
    n_samples = 1000  # 1000个样本
    n_workers = max(1, multiprocessing.cpu_count() - 1)
    
    print("📋 优化配置:")
    print("-" * 80)
    print(f"  采样方法: {sampling_method} (拉丁超立方采样)")
    print(f"  采样数量: {n_samples}")
    print(f"  并行进程: {n_workers}")
    print(f"  预计耗时: {n_samples * 2 / n_workers / 60:.1f} 分钟")
    print()
    
    # 加载数据
    bars = load_all_data()
    
    # 运行优化
    print("=" * 80)
    print("开始参数优化")
    print("=" * 80)
    print()
    
    start_time = datetime.now()
    
    df_results = optimize_parameters(
        bars,
        n_samples=n_samples,
        sampling_method=sampling_method,
        n_workers=n_workers,
        save_interval=50
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f'results/optimization_results_{timestamp}.csv'
    df_results.to_csv(results_file, index=False, encoding='utf-8-sig')
    
    print()
    print("=" * 80)
    print("优化完成！")
    print("=" * 80)
    print(f"总耗时: {elapsed/60:.1f} 分钟")
    print(f"平均速度: {len(df_results)/elapsed:.2f} tests/秒")
    print(f"结果已保存: {results_file}")
    print()
    
    # 分析结果
    top10_return, top10_sharpe = analyze_optimization_results(df_results)
    
    # 可视化
    print()
    print("=" * 80)
    print("生成可视化")
    print("=" * 80)
    print()
    
    fig = visualize_optimization_results(df_results)
    
    # 保存Top结果
    top10_return.to_csv(f'results/top10_by_return_{timestamp}.csv', 
                       index=False, encoding='utf-8-sig')
    top10_sharpe.to_csv(f'results/top10_by_sharpe_{timestamp}.csv', 
                       index=False, encoding='utf-8-sig')
    
    print(f"✅ Top10结果已保存")
    print()
    
    # 显示最佳参数
    print("=" * 80)
    print("🏆 最佳参数配置")
    print("=" * 80)
    print()
    
    best = df_results.loc[df_results['total_return'].idxmax()]
    
    print("按总收益:")
    print(f"  收益: {best['total_return']*100:.2f}%")
    print(f"  Sharpe: {best['sharpe_ratio']:.2f}")
    print(f"  胜率: {best['win_rate']*100:.1f}%")
    print(f"  信号数: {best['n_signals']}")
    print()
    print("参数:")
    print(f"  L_past = {int(best['L_past'])}")
    print(f"  vol_window = {int(best['vol_window'])}")
    print(f"  q_extreme_trend = {best['q_extreme_trend']:.2f}")
    print(f"  min_abs_R_past = {best['min_abs_R_past']:.4f}")
    print(f"  q_manip = {best['q_manip']:.2f}")
    print(f"  min_manip_score = {best['min_manip_score']:.2f}")
    print(f"  holding_horizon = {int(best['holding_horizon'])}")
    print(f"  sl_atr_mult = {best['sl_atr_mult']:.2f}")
    print(f"  tp_atr_mult = {best['tp_atr_mult']:.2f}")
    print()
    
    # 生成配置代码
    print("=" * 80)
    print("📝 最佳配置代码")
    print("=" * 80)
    print()
    print("```python")
    print("config = ExtremeReversalConfig(")
    print(f"    L_past={int(best['L_past'])},")
    print(f"    vol_window={int(best['vol_window'])},")
    print(f"    q_extreme_trend={best['q_extreme_trend']:.2f},")
    print(f"    min_abs_R_past={best['min_abs_R_past']:.4f},")
    print(f"    q_manip={best['q_manip']:.2f},")
    print(f"    min_manip_score={best['min_manip_score']:.2f},")
    print(f"    holding_horizon={int(best['holding_horizon'])},")
    print(f"    sl_atr_mult={best['sl_atr_mult']:.2f},")
    print(f"    tp_atr_mult={best['tp_atr_mult']:.2f},")
    print(")")
    print("```")
    print()
    
    print("=" * 80)
    print("🎉 参数优化完成！")
    print("=" * 80)
    
    # 不显示图表，只保存
    plt.close('all')


if __name__ == "__main__":
    main()

