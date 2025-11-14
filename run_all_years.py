# -*- coding: utf-8 -*-
"""
运行全部年份数据分析 (2015-2025)
Run analysis on all available years (2015-2025)
"""

import sys
import os
from pathlib import Path

# UTF-8 encoding setup for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from run_full_pipeline import run_full_pipeline
import pandas as pd
from datetime import datetime

def main():
    """运行全部年份的数据分析"""
    
    print("=" * 80)
    print("运行全部年份数据分析 (2015-2025)")
    print("Run Analysis on All Years (2015-2025)")
    print("=" * 80)
    print()
    
    # 定义所有年份
    # 注意：2025年数据只到9月
    years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

    print(f"准备处理 {len(years)} 个年份的数据")
    print(f"预计总时长: 约 {len(years) * 2} 分钟")
    print()
    
    # 存储每年的结果
    all_results = []
    
    for year in years:
        print()
        print("=" * 80)
        print(f"处理 {year} 年数据")
        print(f"Processing {year} data")
        print("=" * 80)
        print()
        
        # 定义日期范围
        start_date = f"{year}-01-01"

        # 2025年只到9月
        if year == 2025:
            end_date = f"{year}-09-30"
        else:
            end_date = f"{year}-12-31"

        print(f"日期范围: {start_date} 至 {end_date}")
        
        try:
            # 运行流程
            results = run_full_pipeline(
                start_date=start_date,
                end_date=end_date,
                timeframe='5min',
                save_results=True
            )
            
            # 添加年份信息
            results['year'] = year
            results['start_date'] = start_date
            results['end_date'] = end_date
            
            all_results.append(results)
            
            print()
            print(f"✅ {year} 年处理完成")
            print(f"   Tick 数据: {results.get('n_ticks', 0):,} 条")
            print(f"   K 线数据: {results.get('n_bars', 0):,} 根")
            print(f"   高操纵分数: {results.get('n_high_manip', 0):,} 个")
            print()
            
        except Exception as e:
            print(f"❌ {year} 年处理失败: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 创建汇总表
    if all_results:
        print()
        print("=" * 80)
        print("全部年份分析汇总")
        print("All Years Analysis Summary")
        print("=" * 80)
        print()
        
        # 转换为 DataFrame
        summary_df = pd.DataFrame([
            {
                'year': r['year'],
                'start_date': r['start_date'],
                'end_date': r['end_date'],
                'n_ticks': r.get('n_ticks', 0),
                'n_bars': r.get('n_bars', 0),
                'high_manip_bars': r.get('n_high_manip', 0),
                'n_signals_original': r.get('n_signals_original', 0),
                'n_signals_filtered': r.get('n_signals_filtered', 0),
            }
            for r in all_results
        ])
        
        print(summary_df.to_string(index=False))
        print()
        
        # 保存汇总
        summary_file = 'results/summary_all_years.csv'
        summary_df.to_csv(summary_file, index=False)
        print(f"✅ 汇总已保存至: {summary_file}")
        print()
        
        # 打印总计
        print("总计:")
        print(f"  - Tick 数据: {summary_df['n_ticks'].sum():,} 条")
        print(f"  - K 线数据: {summary_df['n_bars'].sum():,} 根")
        print(f"  - 高操纵分数: {summary_df['high_manip_bars'].sum():,} 个")
        print()
    
    print("=" * 80)
    print("所有年份处理完成！")
    print("All years processed!")
    print("=" * 80)
    print()
    print("下一步:")
    print("  1. 查看 results/ 目录中的各年度 CSV 文件")
    print("  2. 查看 results/summary_all_years.csv 汇总文件")
    print("  3. 使用 Jupyter Notebook 进行可视化分析")
    print()

if __name__ == "__main__":
    main()

