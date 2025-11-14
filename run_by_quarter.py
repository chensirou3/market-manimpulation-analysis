# -*- coding: utf-8 -*-
"""
按季度运行分析 / Run Analysis by Quarter
避免内存问题，分批处理大数据集
"""

import sys
import os

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from pathlib import Path
import pandas as pd
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from run_full_pipeline import run_full_pipeline


def run_by_quarter(year: int = 2024):
    """
    按季度运行分析
    
    Args:
        year: 年份
    """
    quarters = [
        ('Q1', f'{year}-01-01', f'{year}-03-31'),
        ('Q2', f'{year}-04-01', f'{year}-06-30'),
        ('Q3', f'{year}-07-01', f'{year}-09-30'),
        ('Q4', f'{year}-10-01', f'{year}-12-31'),
    ]
    
    all_results = []
    
    print("\n")
    print("=" * 80)
    print(f"按季度运行 {year} 年数据分析")
    print(f"Run {year} Analysis by Quarter")
    print("=" * 80)
    print()
    
    for quarter_name, start_date, end_date in quarters:
        print(f"\n{'=' * 80}")
        print(f"处理 {year} 年 {quarter_name} ({start_date} 至 {end_date})")
        print(f"Processing {year} {quarter_name} ({start_date} to {end_date})")
        print(f"{'=' * 80}\n")
        
        try:
            results = run_full_pipeline(
                start_date=start_date,
                end_date=end_date,
                timeframe='5min',
                save_results=True
            )
            
            if results:
                all_results.append({
                    'quarter': quarter_name,
                    'start_date': start_date,
                    'end_date': end_date,
                    'n_ticks': results.get('n_ticks', 0),
                    'n_bars': results.get('n_bars', 0),
                    'high_manip_bars': results.get('high_manip_bars', 0),
                    'n_signals_original': results.get('n_signals_original', 0),
                    'n_signals_filtered': results.get('n_signals_filtered', 0),
                })
                
                print(f"\n✅ {quarter_name} 处理完成")
                print(f"   Tick 数据: {results.get('n_ticks', 0):,} 条")
                print(f"   K 线数据: {results.get('n_bars', 0):,} 根")
                print(f"   高操纵分数: {results.get('high_manip_bars', 0)} 个")
                print()
            else:
                print(f"\n❌ {quarter_name} 处理失败\n")
                
        except Exception as e:
            print(f"\n❌ {quarter_name} 处理出错: {e}\n")
            import traceback
            traceback.print_exc()
    
    # 汇总结果
    if all_results:
        print("\n")
        print("=" * 80)
        print(f"{year} 年分析汇总")
        print(f"{year} Analysis Summary")
        print("=" * 80)
        print()
        
        df_summary = pd.DataFrame(all_results)
        print(df_summary.to_string(index=False))
        print()
        
        # 保存汇总
        summary_file = f'results/summary_{year}_by_quarter.csv'
        df_summary.to_csv(summary_file, index=False)
        print(f"✅ 汇总已保存至: {summary_file}")
        print()
        
        # 总计
        total_ticks = df_summary['n_ticks'].sum()
        total_bars = df_summary['n_bars'].sum()
        total_high_manip = df_summary['high_manip_bars'].sum()
        
        print("总计:")
        print(f"  - Tick 数据: {total_ticks:,} 条")
        print(f"  - K 线数据: {total_bars:,} 根")
        print(f"  - 高操纵分数: {total_high_manip} 个")
        print()
        
    print("=" * 80)
    print("所有季度处理完成！")
    print("All quarters processed!")
    print("=" * 80)
    print()
    print("下一步:")
    print("  1. 查看 results/ 目录中的各季度 CSV 文件")
    print("  2. 查看 results/summary_2024_by_quarter.csv 汇总文件")
    print("  3. 使用 Jupyter Notebook 进行可视化分析")
    print()


if __name__ == "__main__":
    # 从命令行参数获取年份，默认2024
    import sys
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    run_by_quarter(year=year)

