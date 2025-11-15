"""
测试更新后的tick_loader
"""

from src.data_prep.tick_loader import load_tick_data
import pandas as pd

print("=" * 70)
print("测试更新后的 Tick Loader")
print("=" * 70)

# 测试1: 加载单日数据
print("\n【测试 1】加载单日数据 (2024-01-01)")
print("-" * 70)

try:
    df = load_tick_data(start_date='2024-01-01', end_date='2024-01-01')
    
    print(f"\n✅ 成功加载数据！")
    print(f"\n📊 数据信息:")
    print(f"  - 行数: {len(df):,}")
    print(f"  - 列数: {len(df.columns)}")
    print(f"\n📋 列名: {df.columns.tolist()}")
    print(f"\n🔍 前5行:")
    print(df.head())
    
    if 'timestamp' in df.columns:
        print(f"\n⏰ 时间范围:")
        print(f"  - 开始: {df['timestamp'].min()}")
        print(f"  - 结束: {df['timestamp'].max()}")
    
    if 'price' in df.columns:
        print(f"\n💰 价格统计:")
        print(f"  - 最小: {df['price'].min():.2f}")
        print(f"  - 最大: {df['price'].max():.2f}")
        print(f"  - 平均: {df['price'].mean():.2f}")
    
    if 'volume' in df.columns:
        print(f"\n📊 成交量统计:")
        print(f"  - 总量: {df['volume'].sum():.4f}")
        print(f"  - 平均: {df['volume'].mean():.6f}")
    
except Exception as e:
    print(f"\n❌ 加载失败: {e}")
    import traceback
    traceback.print_exc()

# 测试2: 加载一周数据
print("\n\n【测试 2】加载一周数据 (2024-01-01 到 2024-01-07)")
print("-" * 70)

try:
    df_week = load_tick_data(start_date='2024-01-01', end_date='2024-01-07')
    
    print(f"\n✅ 成功加载数据！")
    print(f"\n📊 数据信息:")
    print(f"  - 总行数: {len(df_week):,}")
    print(f"  - 时间范围: {df_week['timestamp'].min()} 到 {df_week['timestamp'].max()}")
    
    # 按日期统计
    df_week['date'] = df_week['timestamp'].dt.date
    daily_counts = df_week.groupby('date').size()
    print(f"\n📅 每日数据量:")
    for date, count in daily_counts.items():
        print(f"  - {date}: {count:,} 行")
    
except Exception as e:
    print(f"\n❌ 加载失败: {e}")
    import traceback
    traceback.print_exc()

# 测试3: 加载一个月数据
print("\n\n【测试 3】加载一个月数据 (2024-01-01 到 2024-01-31)")
print("-" * 70)

try:
    df_month = load_tick_data(start_date='2024-01-01', end_date='2024-01-31')
    
    print(f"\n✅ 成功加载数据！")
    print(f"\n📊 数据信息:")
    print(f"  - 总行数: {len(df_month):,}")
    print(f"  - 时间范围: {df_month['timestamp'].min()} 到 {df_month['timestamp'].max()}")
    print(f"  - 数据大小: {df_month.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
    
except Exception as e:
    print(f"\n❌ 加载失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("测试完成！")
print("=" * 70)

