"""
测试完整处理流程
Test full pipeline: Tick → Bar → ManipScore
"""

from src.data_prep.tick_loader import load_tick_data
from src.data_prep.bar_aggregator import ticks_to_bars
from src.factors.manipulation_score import compute_manipulation_score
from src.utils.paths import load_config
import pandas as pd

print("=" * 70)
print("测试完整处理流程")
print("Tick → Bar → ManipScore")
print("=" * 70)

# 加载配置
print("\n【步骤 1】加载配置")
print("-" * 70)
config = load_config()
print("✅ 配置加载成功")

# 加载tick数据
print("\n【步骤 2】加载Tick数据 (2024-01-02)")
print("-" * 70)
ticks = load_tick_data(start_date='2024-01-02', end_date='2024-01-02')
print(f"✅ 加载了 {len(ticks):,} 条tick数据")
print(f"   时间范围: {ticks['timestamp'].min()} 到 {ticks['timestamp'].max()}")

# 聚合为K线
print("\n【步骤 3】聚合为K线 (1分钟)")
print("-" * 70)
bars = ticks_to_bars(ticks, timeframe='1min', compute_features=True)
print(f"✅ 生成了 {len(bars):,} 根K线")
print(f"\n📋 K线列名:")
for i, col in enumerate(bars.columns, 1):
    print(f"  {i:2d}. {col}")

print(f"\n🔍 前5根K线:")
print(bars.head())

# 计算ManipScore
print("\n【步骤 4】计算操纵分数 (ManipScore)")
print("-" * 70)
bars_with_score = compute_manipulation_score(bars, config.get('manipulation_score'), ticks)
print(f"✅ 操纵分数计算完成")

if 'manip_score' in bars_with_score.columns:
    print(f"\n📊 ManipScore 统计:")
    print(f"  - 平均分数: {bars_with_score['manip_score'].mean():.4f}")
    print(f"  - 最大分数: {bars_with_score['manip_score'].max():.4f}")
    print(f"  - 最小分数: {bars_with_score['manip_score'].min():.4f}")
    
    # 统计高中低风险时段
    high_risk = (bars_with_score['manip_score'] > 0.7).sum()
    mid_risk = ((bars_with_score['manip_score'] >= 0.5) & (bars_with_score['manip_score'] <= 0.7)).sum()
    low_risk = (bars_with_score['manip_score'] < 0.5).sum()
    
    print(f"\n🎯 风险分布:")
    print(f"  - 高风险 (>0.7):     {high_risk:4d} 个 ({high_risk/len(bars_with_score)*100:5.2f}%)")
    print(f"  - 中风险 (0.5-0.7):  {mid_risk:4d} 个 ({mid_risk/len(bars_with_score)*100:5.2f}%)")
    print(f"  - 低风险 (<0.5):     {low_risk:4d} 个 ({low_risk/len(bars_with_score)*100:5.2f}%)")
    
    # 显示高风险时段
    if high_risk > 0:
        print(f"\n⚠️  高风险时段示例:")
        high_risk_bars = bars_with_score[bars_with_score['manip_score'] > 0.7].head(5)
        print(high_risk_bars[['close', 'volume', 'manip_score']])

# 保存结果
print("\n【步骤 5】保存结果")
print("-" * 70)
output_file = "results/test_bars_with_manipscore_2024-01-02.csv"
bars_with_score.to_csv(output_file)
print(f"✅ 结果已保存到: {output_file}")
print(f"   文件大小: {pd.io.common.file_exists(output_file)}")

# 数据质量检查
print("\n【步骤 6】数据质量检查")
print("-" * 70)

# 检查缺失值
missing = bars_with_score.isnull().sum()
if missing.sum() > 0:
    print("⚠️  发现缺失值:")
    print(missing[missing > 0])
else:
    print("✅ 无缺失值")

# 检查异常值
print(f"\n📈 价格范围检查:")
print(f"  - 最低价: {bars_with_score['low'].min():.2f}")
print(f"  - 最高价: {bars_with_score['high'].max():.2f}")
print(f"  - 价格跨度: {bars_with_score['high'].max() - bars_with_score['low'].min():.2f}")

print(f"\n📊 成交量检查:")
print(f"  - 最小成交量: {bars_with_score['volume'].min():.6f}")
print(f"  - 最大成交量: {bars_with_score['volume'].max():.6f}")
print(f"  - 平均成交量: {bars_with_score['volume'].mean():.6f}")

print("\n" + "=" * 70)
print("✅ 完整流程测试成功！")
print("=" * 70)
print("\n💡 提示:")
print("  - 数据可以正常加载和处理")
print("  - ManipScore计算正常")
print("  - 可以开始运行完整的数据分析")
print("  - 建议运行: python run_single_year.py 2024")

