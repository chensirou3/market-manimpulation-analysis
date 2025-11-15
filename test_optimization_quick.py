"""
快速测试参数优化系统
Quick test for parameter optimization system
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

from parameter_optimization import (
    optimize_parameters,
    analyze_optimization_results,
    visualize_optimization_results
)


def load_sample_data():
    """加载样本数据（仅2024年）"""
    print("加载样本数据 (2024年)...")
    
    results_dir = Path('results')
    files_2024 = sorted(results_dir.glob('bars_with_manipscore_2024*.csv'))
    
    dfs = []
    for file in files_2024:
        df = pd.read_csv(file, index_col=0, parse_dates=True)
        dfs.append(df)
    
    bars = pd.concat(dfs, axis=0)
    bars = bars.sort_index()
    
    if 'returns' not in bars.columns and 'close' in bars.columns:
        bars['returns'] = bars['close'].pct_change()
    
    print(f"✅ 加载完成: {len(bars):,} 根K线")
    return bars


def main():
    """快速测试"""
    
    print("=" * 80)
    print("参数优化系统 - 快速测试")
    print("=" * 80)
    print()
    
    # 加载样本数据
    bars = load_sample_data()
    print()
    
    # 运行小规模优化测试
    print("运行小规模优化测试 (50个样本)...")
    print()
    
    start_time = datetime.now()
    
    df_results = optimize_parameters(
        bars,
        n_samples=50,  # 仅50个样本用于测试
        sampling_method='lhs',
        n_workers=4,
        save_interval=10
    )
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print()
    print(f"✅ 测试完成！耗时: {elapsed:.1f} 秒")
    print(f"   有效结果: {len(df_results)}")
    print()
    
    if len(df_results) > 0:
        # 保存结果
        df_results.to_csv('results/test_optimization_results.csv', index=False)
        print("✅ 结果已保存: results/test_optimization_results.csv")
        print()
        
        # 分析
        analyze_optimization_results(df_results)
        
        # 可视化
        visualize_optimization_results(df_results, 
                                      save_path='results/test_optimization_analysis.png')
        
        print()
        print("=" * 80)
        print("🎉 测试成功！系统运行正常")
        print("=" * 80)
        print()
        print("现在可以运行完整优化:")
        print("  python run_parameter_optimization.py")
    else:
        print("❌ 没有有效结果，请检查参数设置")


if __name__ == "__main__":
    main()

