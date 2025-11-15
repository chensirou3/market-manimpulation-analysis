"""
生成最终分析报告
Generate final analysis report
"""

import pandas as pd
from pathlib import Path
import numpy as np
from datetime import datetime

print("=" * 80)
print("全数据分析最终报告")
print("Full Data Analysis Final Report")
print("=" * 80)
print()

results_dir = Path('results')
csv_files = sorted(results_dir.glob('bars_with_manipscore_*.csv'))

print(f"📁 找到 {len(csv_files)} 个结果文件")
print()

# 收集所有统计数据
all_stats = []

print("📊 正在分析数据...")
for i, csv_file in enumerate(csv_files, 1):
    if i % 5 == 0:
        print(f"  进度: {i}/{len(csv_files)} ({i/len(csv_files)*100:.1f}%)")
    
    try:
        df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
        
        # 从文件名提取信息
        filename = csv_file.stem  # bars_with_manipscore_2024-01-01_2024-03-31
        parts = filename.split('_')
        start_date = parts[2]
        end_date = parts[3]
        year = int(start_date[:4])
        
        # 确定季度
        month = int(start_date[5:7])
        if month <= 3:
            quarter = 'Q1'
        elif month <= 6:
            quarter = 'Q2'
        elif month <= 9:
            quarter = 'Q3'
        else:
            quarter = 'Q4'
        
        # 统计
        stats = {
            'year': year,
            'quarter': quarter,
            'start_date': start_date,
            'end_date': end_date,
            'n_bars': len(df),
            'avg_manip_score': df['manip_score'].mean() if 'manip_score' in df.columns else np.nan,
            'max_manip_score': df['manip_score'].max() if 'manip_score' in df.columns else np.nan,
            'min_manip_score': df['manip_score'].min() if 'manip_score' in df.columns else np.nan,
            'high_risk': (df['manip_score'] > 0.7).sum() if 'manip_score' in df.columns else 0,
            'mid_risk': ((df['manip_score'] >= 0.5) & (df['manip_score'] <= 0.7)).sum() if 'manip_score' in df.columns else 0,
            'low_risk': (df['manip_score'] < 0.5).sum() if 'manip_score' in df.columns else 0,
            'file_size_mb': csv_file.stat().st_size / 1024 / 1024
        }
        
        all_stats.append(stats)
        
    except Exception as e:
        print(f"  ⚠️ 处理 {csv_file.name} 失败: {e}")

print(f"✅ 分析完成\n")

# 创建DataFrame
stats_df = pd.DataFrame(all_stats)

# 总体统计
print("=" * 80)
print("📊 总体统计")
print("=" * 80)
total_bars = stats_df['n_bars'].sum()
total_high = stats_df['high_risk'].sum()
total_mid = stats_df['mid_risk'].sum()
total_low = stats_df['low_risk'].sum()
total_size = stats_df['file_size_mb'].sum()

print(f"  处理季度数: {len(stats_df)}")
print(f"  总K线数: {total_bars:,}")
print(f"  平均ManipScore: {stats_df['avg_manip_score'].mean():.4f}")
print(f"  最大ManipScore: {stats_df['max_manip_score'].max():.4f}")
print(f"  结果文件总大小: {total_size:.2f} MB")
print()

print("=" * 80)
print("⚠️ 风险分布")
print("=" * 80)
print(f"  高风险 (>0.7):    {total_high:8,} 个 ({total_high/total_bars*100:6.2f}%)")
print(f"  中风险 (0.5-0.7): {total_mid:8,} 个 ({total_mid/total_bars*100:6.2f}%)")
print(f"  低风险 (<0.5):    {total_low:8,} 个 ({total_low/total_bars*100:6.2f}%)")
print(f"  总计:             {total_bars:8,} 个")
print()

# 按年份统计
print("=" * 80)
print("📅 按年份统计")
print("=" * 80)
yearly = stats_df.groupby('year').agg({
    'n_bars': 'sum',
    'avg_manip_score': 'mean',
    'high_risk': 'sum',
    'mid_risk': 'sum',
    'low_risk': 'sum'
})
yearly['high_risk_rate'] = yearly['high_risk'] / yearly['n_bars'] * 100
yearly = yearly.sort_index()

print(yearly.to_string())
print()

# 保存详细统计
output_file = results_dir / 'final_statistics.csv'
stats_df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"✅ 详细统计已保存: {output_file}")
print()

# 生成Markdown报告
report_file = 'FINAL_ANALYSIS_REPORT.md'
with open(report_file, 'w', encoding='utf-8') as f:
    f.write("# 全数据分析最终报告\n\n")
    f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write("---\n\n")
    
    f.write("## 📊 总体统计\n\n")
    f.write(f"- **处理季度数**: {len(stats_df)}\n")
    f.write(f"- **总K线数**: {total_bars:,}\n")
    f.write(f"- **平均ManipScore**: {stats_df['avg_manip_score'].mean():.4f}\n")
    f.write(f"- **最大ManipScore**: {stats_df['max_manip_score'].max():.4f}\n")
    f.write(f"- **结果文件总大小**: {total_size:.2f} MB\n\n")
    
    f.write("## ⚠️ 风险分布\n\n")
    f.write(f"| 风险等级 | 数量 | 占比 |\n")
    f.write(f"|---------|------|------|\n")
    f.write(f"| 高风险 (>0.7) | {total_high:,} | {total_high/total_bars*100:.2f}% |\n")
    f.write(f"| 中风险 (0.5-0.7) | {total_mid:,} | {total_mid/total_bars*100:.2f}% |\n")
    f.write(f"| 低风险 (<0.5) | {total_low:,} | {total_low/total_bars*100:.2f}% |\n")
    f.write(f"| **总计** | **{total_bars:,}** | **100.00%** |\n\n")
    
    f.write("## 📅 按年份统计\n\n")
    f.write(yearly.to_markdown())
    f.write("\n\n---\n\n")
    f.write("**报告结束**\n")

print(f"✅ Markdown报告已保存: {report_file}")
print()

print("=" * 80)
print("🎉 报告生成完成！")
print("=" * 80)

