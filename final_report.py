"""最终分析报告"""
import pandas as pd
from pathlib import Path
import re

print("=" * 80)
print("全数据处理最终报告 (2015-2025)")
print("=" * 80)
print()

results_dir = Path('results')
files = sorted(results_dir.glob('bars_with_manipscore_*.csv'))

print(f"📁 结果文件数: {len(files)}")
print()

# 按年份组织
yearly_data = {}

print("📊 正在分析数据...")
for i, f in enumerate(files, 1):
    if i % 10 == 0:
        print(f"  进度: {i}/{len(files)}")
    
    # 从文件名提取日期: bars_with_manipscore_2015-01-01_2015-03-31.csv
    match = re.search(r'(\d{4})-\d{2}-\d{2}_(\d{4})-\d{2}-\d{2}', f.name)
    if match:
        year = match.group(1)
    else:
        continue
    
    df = pd.read_csv(f, index_col=0)
    
    if year not in yearly_data:
        yearly_data[year] = {
            'bars': 0,
            'high': 0,
            'mid': 0,
            'low': 0,
            'scores': [],
            'quarters': 0
        }
    
    yearly_data[year]['bars'] += len(df)
    yearly_data[year]['quarters'] += 1
    
    if 'manip_score' in df.columns:
        yearly_data[year]['high'] += (df['manip_score'] > 0.7).sum()
        yearly_data[year]['mid'] += ((df['manip_score'] >= 0.5) & (df['manip_score'] <= 0.7)).sum()
        yearly_data[year]['low'] += (df['manip_score'] < 0.5).sum()
        yearly_data[year]['scores'].extend(df['manip_score'].dropna().tolist())

print("✅ 分析完成\n")

# 总体统计
total_bars = sum(y['bars'] for y in yearly_data.values())
total_high = sum(y['high'] for y in yearly_data.values())
total_mid = sum(y['mid'] for y in yearly_data.values())
total_low = sum(y['low'] for y in yearly_data.values())
all_scores = []
for y in yearly_data.values():
    all_scores.extend(y['scores'])

print("=" * 80)
print("📊 总体统计 (2015-2025)")
print("=" * 80)
print(f"  处理年份: {len(yearly_data)} 年")
print(f"  处理季度: {len(files)} 个")
print(f"  总K线数: {total_bars:,} 根 (5分钟K线)")
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

print("=" * 80)
print("📅 按年份详细统计")
print("=" * 80)
print(f"{'年份':<6} {'季度':<4} {'K线数':>10} {'平均分':>8} {'高风险':>8} {'高风险率':>10}")
print("-" * 80)

for year in sorted(yearly_data.keys()):
    data = yearly_data[year]
    avg_score = sum(data['scores']) / len(data['scores']) if data['scores'] else 0
    high_rate = data['high'] / data['bars'] * 100 if data['bars'] > 0 else 0
    
    print(f"{year:<6} {data['quarters']:<4} {data['bars']:>10,} {avg_score:>8.4f} {data['high']:>8,} {high_rate:>9.2f}%")

print()

# 趋势分析
print("=" * 80)
print("📈 趋势分析")
print("=" * 80)

years_sorted = sorted(yearly_data.keys())
if len(years_sorted) >= 2:
    first_year = years_sorted[0]
    last_year = years_sorted[-1]
    
    first_avg = sum(yearly_data[first_year]['scores']) / len(yearly_data[first_year]['scores'])
    last_avg = sum(yearly_data[last_year]['scores']) / len(yearly_data[last_year]['scores'])
    
    first_high_rate = yearly_data[first_year]['high'] / yearly_data[first_year]['bars'] * 100
    last_high_rate = yearly_data[last_year]['high'] / yearly_data[last_year]['bars'] * 100
    
    print(f"  {first_year}年 → {last_year}年:")
    print(f"    平均ManipScore: {first_avg:.4f} → {last_avg:.4f} (变化: {(last_avg-first_avg)/first_avg*100:+.1f}%)")
    print(f"    高风险率: {first_high_rate:.2f}% → {last_high_rate:.2f}% (变化: {last_high_rate-first_high_rate:+.2f}%)")

print()

# 保存到文件
report_file = 'FINAL_REPORT_2015_2025.txt'
with open(report_file, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("全数据处理最终报告 (2015-2025)\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"总K线数: {total_bars:,}\n")
    f.write(f"平均ManipScore: {sum(all_scores)/len(all_scores):.4f}\n")
    f.write(f"高风险: {total_high:,} ({total_high/total_bars*100:.2f}%)\n")
    f.write(f"中风险: {total_mid:,} ({total_mid/total_bars*100:.2f}%)\n")
    f.write(f"低风险: {total_low:,} ({total_low/total_bars*100:.2f}%)\n")

print(f"✅ 报告已保存: {report_file}")
print()
print("=" * 80)
print("🎉 全数据处理完成！")
print("=" * 80)

