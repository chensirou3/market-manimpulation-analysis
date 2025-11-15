"""
运行参数优化
Run Parameter Optimization

使用多线程并行计算进行大规模参数优化
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime
import sys

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
    print("极端反转策略 - 参数优化系统")
    print("Parameter Optimization System")
    print("=" * 80)
    print()
    
    # 显示参数空间
    print("📋 参数空间:")
    print("-" * 80)
    for param, values in PARAM_GRID.items():
        if isinstance(values, np.ndarray):
            print(f"  {param:20s}: [{values[0]:.2f}, {values[-1]:.2f}] "
                  f"步长={values[1]-values[0]:.2f} 共{len(values)}个值")
        else:
            print(f"  {param:20s}: {values} 共{len(values)}个值")
    
    total_combinations = np.prod([len(v) for v in PARAM_GRID.values()])
    print()
    print(f"⚠️  全网格搜索总组合数: {total_combinations:,}")
    print(f"   预计耗时: {total_combinations * 2 / 60 / 60:.1f} 小时 (单线程)")
    print()
    
    # 用户选择
    print("请选择优化方法:")
    print("  1. 拉丁超立方采样 (LHS) - 推荐，快速覆盖参数空间")
    print("  2. 网格采样 (Grid) - 系统化但较慢")
    print()
    
    choice = input("请输入选择 (1/2) [默认: 1]: ").strip() or "1"
    
    if choice == "1":
        sampling_method = 'lhs'
        n_samples = int(input("请输入采样数量 [默认: 1000]: ").strip() or "1000")
    else:
        sampling_method = 'grid'
        step = int(input("请输入网格步长 [默认: 3]: ").strip() or "3")
        # 重新计算采样数
        n_samples = np.prod([len(list(v)[::step]) for v in PARAM_GRID.values()])
        print(f"网格采样将测试 {n_samples} 个组合")
    
    print()
    
    # 并行进程数
    import multiprocessing
    max_workers = multiprocessing.cpu_count()
    n_workers = int(input(f"请输入并行进程数 [默认: {max_workers-1}]: ").strip() 
                    or str(max_workers-1))
    
    print()
    print(f"✅ 配置完成:")
    print(f"   采样方法: {sampling_method}")
    print(f"   采样数量: {n_samples}")
    print(f"   并行进程: {n_workers}")
    print(f"   预计耗时: {n_samples * 2 / n_workers / 60:.1f} 分钟")
    print()
    
    confirm = input("开始优化? (y/n) [默认: y]: ").strip().lower() or "y"
    if confirm != 'y':
        print("已取消")
        return
    
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
    
    print("=" * 80)
    print("🎉 参数优化完成！")
    print("=" * 80)
    
    plt.show()


if __name__ == "__main__":
    main()

