# -*- coding: utf-8 -*-
"""
简化版：运行所有年份数据分析
Simplified: Run all years analysis
"""

import sys
import os
from pathlib import Path

# UTF-8 encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from run_full_pipeline import run_full_pipeline
import pandas as pd
from datetime import datetime

def process_year(year):
    """处理单个年份的所有季度"""
    quarters = [
        ('Q1', '01-01', '03-31'),
        ('Q2', '04-01', '06-30'),
        ('Q3', '07-01', '09-30'),
        ('Q4', '10-01', '12-31'),
    ]
    
    # 2025年只有3个季度
    if year == 2025:
        quarters = quarters[:3]
    
    year_results = []
    
    for q_name, start_mm_dd, end_mm_dd in quarters:
        start_date = f"{year}-{start_mm_dd}"
        end_date = f"{year}-{end_mm_dd}"
        
        print(f"\n处理 {year} {q_name}: {start_date} 至 {end_date}")
        
        try:
            results = run_full_pipeline(
                start_date=start_date,
                end_date=end_date,
                timeframe='5min',
                save_results=True
            )
            
            results['year'] = year
            results['quarter'] = q_name
            year_results.append(results)
            
            print(f"✅ 完成 - Ticks: {results.get('n_ticks', 0):,}, Bars: {results.get('n_bars', 0):,}, High Manip: {results.get('n_high_manip', 0):,}")
            
        except Exception as e:
            print(f"❌ 失败: {e}")
            continue
    
    return year_results

def main():
    print("=" * 80)
    print("运行全部年份数据分析 (2015-2025)")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 所有年份
    years = list(range(2015, 2026))  # 2015-2025
    
    all_results = []
    
    for i, year in enumerate(years, 1):
        print("\n" + "=" * 80)
        print(f"处理第 {i}/{len(years)} 年: {year}")
        print("=" * 80)
        
        year_results = process_year(year)
        all_results.extend(year_results)
        
        # 保存中间结果
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
            summary_df.to_csv('results/summary_all_years_progress.csv', index=False)
    
    # 最终汇总
    if all_results:
        print("\n" + "=" * 80)
        print("最终汇总")
        print("=" * 80)
        
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
        
        summary_df.to_csv('results/summary_all_years_final.csv', index=False)
        
        print(f"\n处理季度数: {len(all_results)}")
        print(f"总 Ticks: {summary_df['n_ticks'].sum():,}")
        print(f"总 Bars: {summary_df['n_bars'].sum():,}")
        print(f"总 High Manip: {summary_df['high_manip_bars'].sum():,}")
        print(f"\n汇总文件: results/summary_all_years_final.csv")
    
    print("\n" + "=" * 80)
    print("全部完成！")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

if __name__ == "__main__":
    main()

