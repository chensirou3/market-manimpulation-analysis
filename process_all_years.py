# -*- coding: utf-8 -*-
"""
处理所有年份 (2015-2025)
Process all years (2015-2025)
"""

import sys
import os

# UTF-8 encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from run_by_quarter import run_by_quarter
import pandas as pd
import glob

print("=" * 80)
print("处理所有年份数据 (2015-2025)")
print("Process All Years Data (2015-2025)")
print("=" * 80)
print()

# 处理 2015-2024 年
years = list(range(2015, 2025))  # 2015-2024

for i, year in enumerate(years, 1):
    print(f"\n{'='*80}")
    print(f"处理第 {i}/{len(years)} 年: {year}")
    print(f"Processing year {i}/{len(years)}: {year}")
    print(f"{'='*80}\n")
    
    try:
        run_by_quarter(year=year)
        print(f"\n✅ {year} 年完成")
    except Exception as e:
        print(f"\n❌ {year} 年失败: {e}")
        import traceback
        traceback.print_exc()

# 处理 2025 年 (只有Q1-Q3)
print(f"\n{'='*80}")
print(f"处理 2025 年 (Q1-Q3)")
print(f"Processing 2025 (Q1-Q3)")
print(f"{'='*80}\n")

try:
    # 手动处理2025年的3个季度
    from run_full_pipeline import run_full_pipeline
    
    quarters_2025 = [
        ('Q1', '2025-01-01', '2025-03-31'),
        ('Q2', '2025-04-01', '2025-06-30'),
        ('Q3', '2025-07-01', '2025-09-30'),
    ]
    
    results_2025 = []
    
    for q_name, start_date, end_date in quarters_2025:
        print(f"\n处理 2025 {q_name} ({start_date} 至 {end_date})")
        
        try:
            results = run_full_pipeline(
                start_date=start_date,
                end_date=end_date,
                timeframe='5min',
                save_results=True
            )
            
            results['quarter'] = q_name
            results_2025.append(results)
            
            print(f"✅ 2025 {q_name} 完成")
            print(f"   Ticks: {results.get('n_ticks', 0):,}")
            print(f"   Bars: {results.get('n_bars', 0):,}")
            
        except Exception as e:
            print(f"❌ 2025 {q_name} 失败: {e}")
    
    # 保存2025年汇总
    if results_2025:
        summary_2025 = pd.DataFrame([
            {
                'quarter': r['quarter'],
                'n_ticks': r.get('n_ticks', 0),
                'n_bars': r.get('n_bars', 0),
                'high_manip_bars': r.get('n_high_manip', 0),
            }
            for r in results_2025
        ])
        summary_2025.to_csv('results/summary_2025_by_quarter.csv', index=False)
        print(f"\n✅ 2025 年完成")
        
except Exception as e:
    print(f"\n❌ 2025 年失败: {e}")
    import traceback
    traceback.print_exc()

# 合并所有汇总文件
print(f"\n{'='*80}")
print("合并所有汇总文件")
print("Merging all summary files")
print(f"{'='*80}\n")

try:
    summary_files = glob.glob('results/summary_*_by_quarter.csv')
    print(f"找到 {len(summary_files)} 个汇总文件")
    
    if summary_files:
        dfs = []
        for f in summary_files:
            df = pd.read_csv(f)
            # 从文件名提取年份
            if '2015' in f:
                df['year'] = 2015
            elif '2016' in f:
                df['year'] = 2016
            elif '2017' in f:
                df['year'] = 2017
            elif '2018' in f:
                df['year'] = 2018
            elif '2019' in f:
                df['year'] = 2019
            elif '2020' in f:
                df['year'] = 2020
            elif '2021' in f:
                df['year'] = 2021
            elif '2022' in f:
                df['year'] = 2022
            elif '2023' in f:
                df['year'] = 2023
            elif '2024' in f:
                df['year'] = 2024
            elif '2025' in f:
                df['year'] = 2025
            dfs.append(df)
        
        final_summary = pd.concat(dfs, ignore_index=True)
        final_summary = final_summary.sort_values(['year', 'quarter'])
        final_summary.to_csv('results/summary_all_years.csv', index=False)
        
        print(f"✅ 汇总文件已保存: results/summary_all_years.csv")
        print(f"\n总计:")
        print(f"  处理季度数: {len(final_summary)}")
        print(f"  总 Ticks: {final_summary['n_ticks'].sum():,}")
        print(f"  总 Bars: {final_summary['n_bars'].sum():,}")
        print(f"  总 High Manip: {final_summary['high_manip_bars'].sum():,}")
        
except Exception as e:
    print(f"❌ 合并失败: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print("全部完成！")
print("All Done!")
print(f"{'='*80}\n")

