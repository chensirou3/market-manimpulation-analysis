"""简单统计报告"""
import pandas as pd
from pathlib import Path

print("=" * 80)
print("全数据处理结果统计")
print("=" * 80)
print()

results_dir = Path('results')
files = sorted(results_dir.glob('bars_with_manipscore_*.csv'))

print(f"📁 结果文件数: {len(files)}")
print()

# 统计
total_bars = 0
total_high = 0
total_mid = 0
total_low = 0
all_scores = []

print("📊 正在统计...")
for i, f in enumerate(files, 1):
    if i % 10 == 0:
        print(f"  {i}/{len(files)}")
    
    df = pd.read_csv(f, index_col=0)
    total_bars += len(df)
    
    if 'manip_score' in df.columns:
        total_high += (df['manip_score'] > 0.7).sum()
        total_mid += ((df['manip_score'] >= 0.5) & (df['manip_score'] <= 0.7)).sum()
        total_low += (df['manip_score'] < 0.5).sum()
        all_scores.extend(df['manip_score'].dropna().tolist())

print("✅ 统计完成\n")

print("=" * 80)
print("📊 总体统计")
print("=" * 80)
print(f"  总K线数: {total_bars:,}")
print(f"  平均ManipScore: {sum(all_scores)/len(all_scores):.4f}")
print(f"  最大ManipScore: {max(all_scores):.4f}")
print(f"  最小ManipScore: {min(all_scores):.4f}")
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

yearly_stats = {}
for f in files:
    # 从文件名提取年份
    name = f.stem
    year = name.split('_')[2][:4]
    
    df = pd.read_csv(f, index_col=0)
    
    if year not in yearly_stats:
        yearly_stats[year] = {'bars': 0, 'high': 0, 'mid': 0, 'low': 0, 'scores': []}
    
    yearly_stats[year]['bars'] += len(df)
    
    if 'manip_score' in df.columns:
        yearly_stats[year]['high'] += (df['manip_score'] > 0.7).sum()
        yearly_stats[year]['mid'] += ((df['manip_score'] >= 0.5) & (df['manip_score'] <= 0.7)).sum()
        yearly_stats[year]['low'] += (df['manip_score'] < 0.5).sum()
        yearly_stats[year]['scores'].extend(df['manip_score'].dropna().tolist())

for year in sorted(yearly_stats.keys()):
    stats = yearly_stats[year]
    avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
    high_rate = stats['high'] / stats['bars'] * 100 if stats['bars'] > 0 else 0
    
    print(f"{year}: K线={stats['bars']:6,}, 平均分={avg_score:.4f}, 高风险={stats['high']:4,} ({high_rate:5.2f}%)")

print()
print("=" * 80)
print("🎉 统计完成！")
print("=" * 80)

