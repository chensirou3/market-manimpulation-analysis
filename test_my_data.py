"""
测试实际数据加载
Test loading actual data from the data directory
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def load_data_from_symbol_date_structure(start_date, end_date=None):
    """
    从 symbol=XAUUSD/date=YYYY-MM-DD/ 结构加载数据
    """
    data_dir = Path("data")
    symbol_dir = data_dir / "symbol=XAUUSD"
    
    if not symbol_dir.exists():
        print(f"❌ 目录不存在: {symbol_dir}")
        return None
    
    # 转换日期
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date) if end_date else start_date
    
    # 生成日期范围
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    dfs = []
    files_loaded = 0
    
    print(f"\n🔍 搜索日期范围: {start_date.date()} 到 {end_date.date()}")
    print(f"   共 {len(date_range)} 天\n")
    
    for date in date_range:
        date_str = date.strftime('%Y-%m-%d')
        date_dir = symbol_dir / f"date={date_str}"
        
        if not date_dir.exists():
            print(f"  ⚠️  {date_str}: 目录不存在")
            continue
        
        # 查找该日期的所有parquet文件
        parquet_files = list(date_dir.glob("*.parquet"))
        
        if not parquet_files:
            print(f"  ⚠️  {date_str}: 没有找到parquet文件")
            continue
        
        # 加载所有文件
        for file_path in parquet_files:
            try:
                df_part = pd.read_parquet(file_path)
                dfs.append(df_part)
                files_loaded += 1
                print(f"  ✅ {date_str}: 加载 {file_path.name} ({len(df_part):,} 行)")
            except Exception as e:
                print(f"  ❌ {date_str}: 加载失败 - {e}")
    
    if not dfs:
        print("\n❌ 没有加载到任何数据！")
        return None
    
    # 合并所有数据
    df = pd.concat(dfs, ignore_index=True)
    print(f"\n✅ 成功加载 {files_loaded} 个文件，共 {len(df):,} 行数据")
    
    return df


def adapt_columns(df):
    """
    将列名适配为标准格式
    """
    df = df.copy()
    
    # 处理时间戳
    if 'ts' in df.columns:
        df['timestamp'] = df['ts']
    
    # 计算中间价
    if 'bid' in df.columns and 'ask' in df.columns:
        df['price'] = (df['bid'] + df['ask']) / 2
    
    # 计算成交量
    if 'bid_size' in df.columns and 'ask_size' in df.columns:
        df['volume'] = df['bid_size'] + df['ask_size']
    
    # 计算价差
    if 'bid' in df.columns and 'ask' in df.columns:
        df['spread'] = df['ask'] - df['bid']
    
    return df


if __name__ == "__main__":
    print("=" * 70)
    print("测试数据加载 - 实际数据结构")
    print("=" * 70)
    
    # 测试1: 加载单日数据
    print("\n【测试 1】加载单日数据 (2024-01-01)")
    print("-" * 70)
    df = load_data_from_symbol_date_structure('2024-01-01')
    
    if df is not None:
        print("\n📊 原始数据信息:")
        print(f"  - 行数: {len(df):,}")
        print(f"  - 列数: {len(df.columns)}")
        print(f"\n📋 列名: {df.columns.tolist()}")
        print(f"\n🔍 前5行:")
        print(df.head())
        
        # 适配列名
        df = adapt_columns(df)
        
        print(f"\n📊 适配后数据信息:")
        print(f"  - 行数: {len(df):,}")
        print(f"  - 列数: {len(df.columns)}")
        print(f"\n📋 新列名: {df.columns.tolist()}")
        
        if 'timestamp' in df.columns:
            print(f"\n⏰ 时间范围:")
            print(f"  - 开始: {df['timestamp'].min()}")
            print(f"  - 结束: {df['timestamp'].max()}")
        
        if 'price' in df.columns:
            print(f"\n💰 价格统计:")
            print(f"  - 最小: {df['price'].min():.2f}")
            print(f"  - 最大: {df['price'].max():.2f}")
            print(f"  - 平均: {df['price'].mean():.2f}")
    
    # 测试2: 加载一周数据
    print("\n\n【测试 2】加载一周数据 (2024-01-01 到 2024-01-07)")
    print("-" * 70)
    df_week = load_data_from_symbol_date_structure('2024-01-01', '2024-01-07')
    
    if df_week is not None:
        df_week = adapt_columns(df_week)
        print(f"\n📊 一周数据汇总:")
        print(f"  - 总行数: {len(df_week):,}")
        print(f"  - 时间范围: {df_week['timestamp'].min()} 到 {df_week['timestamp'].max()}")
        
        # 按日期统计
        df_week['date'] = df_week['timestamp'].dt.date
        daily_counts = df_week.groupby('date').size()
        print(f"\n📅 每日数据量:")
        for date, count in daily_counts.items():
            print(f"  - {date}: {count:,} 行")
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)

