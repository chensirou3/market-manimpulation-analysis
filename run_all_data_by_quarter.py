# -*- coding: utf-8 -*-
"""
按季度运行全部数据分析 (2015-2025)
Run analysis on all data by quarter (2015-2025)
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

def main():
    """按季度运行全部数据分析"""
    
    print("=" * 80)
    print("按季度运行全部数据分析 (2015-2025)")
    print("Run Analysis on All Data by Quarter (2015-2025)")
    print("=" * 80)
    print()
    
    # 定义所有年份和季度
    years = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
    quarters = [
        ('Q1', '01-01', '03-31'),
        ('Q2', '04-01', '06-30'),
        ('Q3', '07-01', '09-30'),
        ('Q4', '10-01', '12-31'),
    ]
    
    # 2025年只有Q1-Q3
    years_2025 = [(2025, [
        ('Q1', '01-01', '03-31'),
        ('Q2', '04-01', '06-30'),
        ('Q3', '07-01', '09-30'),
    ])]
    
    total_quarters = len(years) * 4 + 3  # 10年*4季度 + 2025年3季度 = 43季度
    print(f"准备处理 {total_quarters} 个季度的数据")
    print(f"预计总时长: 约 {total_quarters * 0.5:.0f} 分钟")
    print()
    
    # 存储所有结果
    all_results = []
    processed = 0
    
    # 处理2015-2024年
    for year in years:
        for q_name, start_mm_dd, end_mm_dd in quarters:
            processed += 1
            
            print()
            print("=" * 80)
            print(f"处理 {year} 年 {q_name} ({processed}/{total_quarters})")
            print(f"Processing {year} {q_name} ({processed}/{total_quarters})")
            print("=" * 80)
            print()
            
            start_date = f"{year}-{start_mm_dd}"
            end_date = f"{year}-{end_mm_dd}"
            
            try:
                results = run_full_pipeline(
                    start_date=start_date,
                    end_date=end_date,
                    timeframe='5min',
                    save_results=True
                )
                
                results['year'] = year
                results['quarter'] = q_name
                results['start_date'] = start_date
                results['end_date'] = end_date
                
                all_results.append(results)
                
                print()
                print(f"✅ {year} {q_name} 处理完成")
                print(f"   Tick 数据: {results.get('n_ticks', 0):,} 条")
                print(f"   K 线数据: {results.get('n_bars', 0):,} 根")
                print(f"   高操纵分数: {results.get('n_high_manip', 0):,} 个")
                print()
                
            except Exception as e:
                print(f"❌ {year} {q_name} 处理失败: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    # 处理2025年
    for year, year_quarters in years_2025:
        for q_name, start_mm_dd, end_mm_dd in year_quarters:
            processed += 1
            
            print()
            print("=" * 80)
            print(f"处理 {year} 年 {q_name} ({processed}/{total_quarters})")
            print(f"Processing {year} {q_name} ({processed}/{total_quarters})")
            print("=" * 80)
            print()
            
            start_date = f"{year}-{start_mm_dd}"
            end_date = f"{year}-{end_mm_dd}"
            
            try:
                results = run_full_pipeline(
                    start_date=start_date,
                    end_date=end_date,
                    timeframe='5min',
                    save_results=True
                )
                
                results['year'] = year
                results['quarter'] = q_name
                results['start_date'] = start_date
                results['end_date'] = end_date
                
                all_results.append(results)
                
                print()
                print(f"✅ {year} {q_name} 处理完成")
                print(f"   Tick 数据: {results.get('n_ticks', 0):,} 条")
                print(f"   K 线数据: {results.get('n_bars', 0):,} 根")
                print(f"   高操纵分数: {results.get('n_high_manip', 0):,} 个")
                print()
                
            except Exception as e:
                print(f"❌ {year} {q_name} 处理失败: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    # 创建汇总表
    if all_results:
        print()
        print("=" * 80)
        print("全部数据分析汇总")
        print("All Data Analysis Summary")
        print("=" * 80)
        print()
        
        # 转换为 DataFrame
        summary_df = pd.DataFrame([
            {
                'year': r['year'],
                'quarter': r['quarter'],
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
        summary_file = 'results/summary_all_data.csv'
        summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
        print(f"✅ 汇总已保存至: {summary_file}")
        print()
        
        # 打印总计
        print("总计:")
        print(f"  - 处理季度数: {len(all_results)} 个")
        print(f"  - Tick 数据: {summary_df['n_ticks'].sum():,} 条")
        print(f"  - K 线数据: {summary_df['n_bars'].sum():,} 根")
        print(f"  - 高操纵分数: {summary_df['high_manip_bars'].sum():,} 个")
        print()
    
    print("=" * 80)
    print("所有数据处理完成！")
    print("All data processed!")
    print("=" * 80)
    print()
    print("下一步:")
    print("  1. 查看 results/ 目录中的各季度 CSV 文件")
    print("  2. 查看 results/summary_all_data.csv 汇总文件")
    print("  3. 使用 Jupyter Notebook 进行可视化分析")
    print()

if __name__ == "__main__":
    main()

