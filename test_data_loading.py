"""
测试数据加载 / Test Data Loading
验证更新后的 tick_loader 能否正确加载您的数据
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_prep.tick_loader import load_tick_data
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


def test_load_single_day():
    """测试加载单日数据"""
    
    print("=" * 70)
    print("测试 1: 加载单日数据 (2024-01-01)")
    print("=" * 70)
    print()
    
    try:
        df = load_tick_data(
            start_date='2024-01-01',
            end_date='2024-01-01'
        )
        
        print(f"✅ 成功加载数据！")
        print()
        print(f"📊 数据信息:")
        print(f"  - 行数: {len(df):,}")
        print(f"  - 列数: {len(df.columns)}")
        print()
        
        print(f"📋 列名:")
        for col in df.columns:
            print(f"  - {col} ({df[col].dtype})")
        print()
        
        print(f"🔍 前 10 行数据:")
        print(df.head(10))
        print()
        
        print(f"📈 数据统计:")
        print(df[['price', 'volume', 'spread']].describe())
        print()
        
        print(f"⏰ 时间范围:")
        print(f"  - 开始: {df['timestamp'].min()}")
        print(f"  - 结束: {df['timestamp'].max()}")
        print(f"  - 时长: {df['timestamp'].max() - df['timestamp'].min()}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_load_date_range():
    """测试加载日期范围"""
    
    print("=" * 70)
    print("测试 2: 加载日期范围 (2024-01-01 到 2024-01-05)")
    print("=" * 70)
    print()
    
    try:
        df = load_tick_data(
            start_date='2024-01-01',
            end_date='2024-01-05'
        )
        
        print(f"✅ 成功加载数据！")
        print()
        print(f"📊 数据信息:")
        print(f"  - 总行数: {len(df):,}")
        print(f"  - 时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
        print()
        
        # 按日期统计
        df['date'] = df['timestamp'].dt.date
        daily_counts = df.groupby('date').size()
        
        print(f"📅 每日数据量:")
        for date, count in daily_counts.items():
            print(f"  - {date}: {count:,} 条")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_load_recent_data():
    """测试加载最近的数据"""
    
    print("=" * 70)
    print("测试 3: 加载最近数据 (2025-01-01)")
    print("=" * 70)
    print()
    
    try:
        df = load_tick_data(
            start_date='2025-01-01',
            end_date='2025-01-01'
        )
        
        if len(df) > 0:
            print(f"✅ 成功加载数据！")
            print(f"  - 行数: {len(df):,}")
            print(f"  - 时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
        else:
            print(f"⚠️  该日期没有数据")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_quality():
    """测试数据质量"""
    
    print("=" * 70)
    print("测试 4: 数据质量检查")
    print("=" * 70)
    print()
    
    try:
        df = load_tick_data(
            start_date='2024-01-02',  # 选择一个有数据的日期
            end_date='2024-01-02'
        )
        
        if len(df) == 0:
            print("⚠️  没有数据，跳过质量检查")
            return True
        
        print(f"✅ 数据质量检查:")
        print()
        
        # 检查缺失值
        print(f"📋 缺失值检查:")
        missing = df.isnull().sum()
        for col in df.columns:
            if missing[col] > 0:
                print(f"  ⚠️  {col}: {missing[col]} 个缺失值 ({missing[col]/len(df)*100:.2f}%)")
            else:
                print(f"  ✓ {col}: 无缺失值")
        print()
        
        # 检查价格合理性
        print(f"💰 价格检查:")
        print(f"  - 最小价格: {df['price'].min():.5f}")
        print(f"  - 最大价格: {df['price'].max():.5f}")
        print(f"  - 平均价格: {df['price'].mean():.5f}")
        print(f"  - 价格标准差: {df['price'].std():.5f}")
        
        if df['price'].min() <= 0:
            print(f"  ⚠️  发现非正价格！")
        else:
            print(f"  ✓ 价格合理")
        print()
        
        # 检查成交量
        print(f"📊 成交量检查:")
        print(f"  - 最小成交量: {df['volume'].min():.2f}")
        print(f"  - 最大成交量: {df['volume'].max():.2f}")
        print(f"  - 平均成交量: {df['volume'].mean():.2f}")
        
        if df['volume'].min() < 0:
            print(f"  ⚠️  发现负成交量！")
        else:
            print(f"  ✓ 成交量合理")
        print()
        
        # 检查时间序列
        print(f"⏰ 时间序列检查:")
        time_diffs = df['timestamp'].diff().dropna()
        print(f"  - 平均时间间隔: {time_diffs.mean()}")
        print(f"  - 最小时间间隔: {time_diffs.min()}")
        print(f"  - 最大时间间隔: {time_diffs.max()}")
        
        # 检查是否有重复时间戳
        duplicates = df['timestamp'].duplicated().sum()
        if duplicates > 0:
            print(f"  ⚠️  发现 {duplicates} 个重复时间戳")
        else:
            print(f"  ✓ 无重复时间戳")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    
    print("\n")
    print("🚀 开始测试数据加载功能")
    print("=" * 70)
    print()
    
    results = []
    
    # 运行测试
    results.append(("单日数据加载", test_load_single_day()))
    results.append(("日期范围加载", test_load_date_range()))
    results.append(("最近数据加载", test_load_recent_data()))
    results.append(("数据质量检查", test_data_quality()))
    
    # 总结
    print("\n")
    print("=" * 70)
    print("测试总结")
    print("=" * 70)
    print()
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {status} - {test_name}")
    
    print()
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    print(f"总计: {passed}/{total} 个测试通过")
    print()
    
    if passed == total:
        print("🎉 所有测试通过！数据加载功能正常！")
    else:
        print("⚠️  部分测试失败，请检查错误信息")
    
    print()


if __name__ == "__main__":
    main()

