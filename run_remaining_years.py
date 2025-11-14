# -*- coding: utf-8 -*-
"""
处理剩余年份 (2016-2023, 2025)
Process remaining years (2016-2023, 2025)
"""

import sys
import os
import subprocess

# UTF-8 encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 80)
print("处理剩余年份 (2016-2023, 2025)")
print("Process Remaining Years (2016-2023, 2025)")
print("=" * 80)
print()

# 2016-2023年
years = list(range(2016, 2024))  # 2016-2023

for i, year in enumerate(years, 1):
    print(f"\n{'='*80}")
    print(f"处理第 {i}/{len(years)+1} 年: {year}")
    print(f"{'='*80}\n")
    
    # 调用 run_by_quarter.py
    result = subprocess.run(
        [sys.executable, 'run_by_quarter.py', str(year)],
        capture_output=False,
        text=True
    )
    
    if result.returncode == 0:
        print(f"\n✅ {year} 年完成")
    else:
        print(f"\n❌ {year} 年失败")

# 处理 2025 年
print(f"\n{'='*80}")
print(f"处理 2025 年 (Q1-Q3)")
print(f"{'='*80}\n")

from run_full_pipeline import run_full_pipeline
import pandas as pd

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

print(f"\n{'='*80}")
print("全部完成！")
print("All Done!")
print(f"{'='*80}\n")

