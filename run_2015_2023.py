# -*- coding: utf-8 -*-
"""
运行 2015-2023 年数据分析（按季度）
Run 2015-2023 analysis by quarter
"""

import sys
import os

# UTF-8 encoding setup for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from run_full_pipeline import run_full_pipeline
import pandas as pd

print("=" * 80)
print("运行 2015-2023 年数据分析")
print("Run 2015-2023 Analysis")
print("=" * 80)
print()

# 定义年份和季度
years = list(range(2015, 2024))  # 2015-2023
quarters = [
    ('Q1', '01-01', '03-31'),
    ('Q2', '04-01', '06-30'),
    ('Q3', '07-01', '09-30'),
    ('Q4', '10-01', '12-31'),
]

total = len(years) * 4
print(f"准备处理 {len(years)} 年 × 4 季度 = {total} 个季度")
print()

all_results = []
count = 0

for year in years:
    for q_name, start_mm_dd, end_mm_dd in quarters:
        count += 1
        
        print()
        print("=" * 80)
        print(f"处理 {year} 年 {q_name} ({count}/{total})")
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
            all_results.append(results)
            
            print(f"\n✅ {year} {q_name} 完成")
            print(f"   Ticks: {results.get('n_ticks', 0):,}")
            print(f"   Bars: {results.get('n_bars', 0):,}")
            print(f"   High Manip: {results.get('n_high_manip', 0):,}")
            
        except Exception as e:
            print(f"❌ {year} {q_name} 失败: {e}")
            continue

# 保存汇总
if all_results:
    summary_df = pd.DataFrame([
        {
            'year': r['year'],
            'quarter': r['quarter'],
            'n_ticks': r.get('n_ticks', 0),
            'n_bars': r.get('n_bars', 0),
            'high_manip_bars': r.get('n_high_manip', 0),
        }
        for r in all_results
    ])
    
    summary_df.to_csv('results/summary_2015_2023.csv', index=False)
    print(f"\n✅ 汇总已保存: results/summary_2015_2023.csv")
    print(f"\n总计:")
    print(f"  Ticks: {summary_df['n_ticks'].sum():,}")
    print(f"  Bars: {summary_df['n_bars'].sum():,}")
    print(f"  High Manip: {summary_df['high_manip_bars'].sum():,}")

print("\n" + "=" * 80)
print("完成！")
print("=" * 80)

