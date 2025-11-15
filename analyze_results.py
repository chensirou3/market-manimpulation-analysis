"""
分析全部处理结果
Analyze all processing results
"""

import pandas as pd
from pathlib import Path
import numpy as np

print("=" * 80)
print("全数据分析结果报告")
print("Full Data Analysis Results Report")
print("=" * 80)
print()

results_dir = Path('results')

# 1. 读取汇总文件
summary_file = results_dir / 'summary_all_data.csv'
if summary_file.exists():
    summary = pd.read_csv(summary_file)
    
    print("📊 处理汇总统计")
    print("=" * 80)
    print(f"  总季度数: {len(summary)}")
    print(f"  总Tick数: {summary['n_ticks'].sum():,}")
    print(f"  总K线数: {summary['n_bars'].sum():,}")
    print(f"  高操纵时段: {summary['n_high_manip'].sum():,}")
    print()
    
    # 按年份统计
    print("📅 按年份统计")
    print("=" * 80)
    yearly = summary.groupby('year').agg({
        'n_ticks': 'sum',
        'n_bars': 'sum',
        'n_high_manip': 'sum'
    })
    yearly['manip_rate'] = yearly['n_high_manip'] / yearly['n_bars'] * 100
    
    print(yearly.to_string())
    print()

# 2. 读取所有详细数据文件并统计
print("📈 详细数据分析")
print("=" * 80)

all_data = []
csv_files = sorted(results_dir.glob('bars_with_manipscore_*.csv'))

print(f"正在读取 {len(csv_files)} 个文件...")

for i, csv_file in enumerate(csv_files, 1):
    if i % 10 == 0:
        print(f"  已读取 {i}/{len(csv_files)} 个文件...")
    
    try:
        df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
        
        # 提取年份和季度
        filename = csv_file.stem
        parts = filename.split('_')
        start_date = parts[2]
        year = start_date[:4]
        
        # 统计
        stats = {
            'file': csv_file.name,
            'year': year,
            'n_bars': len(df),
            'avg_manip_score': df['manip_score'].mean() if 'manip_score' in df.columns else 0,
            'max_manip_score': df['manip_score'].max() if 'manip_score' in df.columns else 0,
            'high_risk': (df['manip_score'] > 0.7).sum() if 'manip_score' in df.columns else 0,
            'mid_risk': ((df['manip_score'] >= 0.5) & (df['manip_score'] <= 0.7)).sum() if 'manip_score' in df.columns else 0,
            'low_risk': (df['manip_score'] < 0.5).sum() if 'manip_score' in df.columns else 0,
        }
        
        all_data.append(stats)
        
    except Exception as e:
        print(f"  ⚠️ 读取 {csv_file.name} 失败: {e}")

print(f"✅ 完成读取\n")

# 3. 生成统计报告
if all_data:
    stats_df = pd.DataFrame(all_data)
    
    print("🎯 ManipScore 统计")
    print("=" * 80)
    print(f"  平均ManipScore: {stats_df['avg_manip_score'].mean():.4f}")
    print(f"  最大ManipScore: {stats_df['max_manip_score'].max():.4f}")
    print()
    
    total_bars = stats_df['n_bars'].sum()
    total_high = stats_df['high_risk'].sum()
    total_mid = stats_df['mid_risk'].sum()
    total_low = stats_df['low_risk'].sum()
    
    print("⚠️ 风险分布")
    print("=" * 80)
    print(f"  高风险 (>0.7):    {total_high:8,} 个 ({total_high/total_bars*100:5.2f}%)")
    print(f"  中风险 (0.5-0.7): {total_mid:8,} 个 ({total_mid/total_bars*100:5.2f}%)")
    print(f"  低风险 (<0.5):    {total_low:8,} 个 ({total_low/total_bars*100:5.2f}%)")
    print(f"  总计:             {total_bars:8,} 个")
    print()
    
    # 按年份统计ManipScore
    print("📊 按年份ManipScore统计")
    print("=" * 80)
    yearly_manip = stats_df.groupby('year').agg({
        'avg_manip_score': 'mean',
        'high_risk': 'sum',
        'n_bars': 'sum'
    })
    yearly_manip['high_risk_rate'] = yearly_manip['high_risk'] / yearly_manip['n_bars'] * 100
    yearly_manip = yearly_manip.sort_index()
    
    print(yearly_manip.to_string())
    print()
    
    # 保存详细统计
    stats_file = results_dir / 'detailed_statistics.csv'
    stats_df.to_csv(stats_file, index=False, encoding='utf-8-sig')
    print(f"✅ 详细统计已保存: {stats_file}")
    print()

# 4. 文件大小统计
print("💾 文件大小统计")
print("=" * 80)
total_size = sum(f.stat().st_size for f in csv_files)
print(f"  结果文件总大小: {total_size / 1024 / 1024:.2f} MB")
print(f"  平均文件大小: {total_size / len(csv_files) / 1024 / 1024:.2f} MB")
print()

print("=" * 80)
print("🎉 分析完成！")
print("=" * 80)

