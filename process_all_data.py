"""
全数据处理脚本 - 简化版
Process all data - Simplified version
"""

from run_full_pipeline import run_full_pipeline
import pandas as pd
from datetime import datetime
import sys

print("=" * 80)
print("全数据处理 (2015-2025)")
print("Processing All Data (2015-2025)")
print("=" * 80)
print()

# 定义所有年份和季度
years = list(range(2015, 2025))  # 2015-2024
quarters = [
    ('Q1', '01-01', '03-31'),
    ('Q2', '04-01', '06-30'),
    ('Q3', '07-01', '09-30'),
    ('Q4', '10-01', '12-31'),
]

# 2025年
years_2025 = [
    ('Q1', '01-01', '03-31'),
    ('Q2', '04-01', '06-30'),
    ('Q3', '07-01', '09-30'),
]

total_quarters = len(years) * 4 + len(years_2025)
print(f"📊 总共 {total_quarters} 个季度")
print(f"⏱️  预计时间: {total_quarters * 0.5:.0f}-{total_quarters:.0f} 分钟")
print()

all_results = []
processed = 0
failed = 0
start_time = datetime.now()

# 处理2015-2024年
for year in years:
    for q_name, start_mm_dd, end_mm_dd in quarters:
        processed += 1
        
        print(f"\n{'='*80}")
        print(f"处理 {year} {q_name} ({processed}/{total_quarters})")
        print(f"{'='*80}")
        
        start_date = f"{year}-{start_mm_dd}"
        end_date = f"{year}-{end_mm_dd}"
        
        try:
            q_start = datetime.now()
            
            results = run_full_pipeline(
                start_date=start_date,
                end_date=end_date,
                timeframe='5min',
                save_results=True
            )
            
            q_time = (datetime.now() - q_start).total_seconds()
            
            results['year'] = year
            results['quarter'] = q_name
            results['start_date'] = start_date
            results['end_date'] = end_date
            results['time'] = q_time
            
            all_results.append(results)
            
            print(f"\n✅ 完成 (耗时: {q_time:.1f}秒)")
            print(f"   Ticks: {results.get('n_ticks', 0):,}")
            print(f"   Bars: {results.get('n_bars', 0):,}")
            print(f"   高风险: {results.get('n_high_manip', 0):,}")
            
            # 进度
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            avg = elapsed / processed
            remaining = (total_quarters - processed) * avg
            print(f"   进度: {processed}/{total_quarters} ({processed/total_quarters*100:.1f}%)")
            print(f"   已用: {elapsed:.1f}分钟, 剩余: {remaining:.1f}分钟")
            
        except Exception as e:
            failed += 1
            print(f"\n❌ 失败: {e}")
            continue

# 处理2025年
for q_name, start_mm_dd, end_mm_dd in years_2025:
    processed += 1
    year = 2025
    
    print(f"\n{'='*80}")
    print(f"处理 {year} {q_name} ({processed}/{total_quarters})")
    print(f"{'='*80}")
    
    start_date = f"{year}-{start_mm_dd}"
    end_date = f"{year}-{end_mm_dd}"
    
    try:
        q_start = datetime.now()
        
        results = run_full_pipeline(
            start_date=start_date,
            end_date=end_date,
            timeframe='5min',
            save_results=True
        )
        
        q_time = (datetime.now() - q_start).total_seconds()
        
        results['year'] = year
        results['quarter'] = q_name
        results['start_date'] = start_date
        results['end_date'] = end_date
        results['time'] = q_time
        
        all_results.append(results)
        
        print(f"\n✅ 完成 (耗时: {q_time:.1f}秒)")
        print(f"   Ticks: {results.get('n_ticks', 0):,}")
        print(f"   Bars: {results.get('n_bars', 0):,}")
        print(f"   高风险: {results.get('n_high_manip', 0):,}")
        
    except Exception as e:
        failed += 1
        print(f"\n❌ 失败: {e}")
        continue

# 保存汇总
if all_results:
    print(f"\n{'='*80}")
    print("保存汇总...")
    print(f"{'='*80}\n")
    
    summary_df = pd.DataFrame(all_results)
    summary_file = 'results/summary_all_data.csv'
    summary_df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    
    print(f"✅ 汇总已保存: {summary_file}\n")
    
    total_time = (datetime.now() - start_time).total_seconds() / 60
    print(f"{'='*80}")
    print("总计:")
    print(f"  成功: {len(all_results)}, 失败: {failed}")
    print(f"  Ticks: {summary_df['n_ticks'].sum():,}")
    print(f"  Bars: {summary_df['n_bars'].sum():,}")
    print(f"  总耗时: {total_time:.1f}分钟")
    print(f"{'='*80}\n")

print("🎉 处理完成！")

