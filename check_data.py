"""
数据检查脚本 / Data Check Script
检查 data 目录中的数据文件是否可用
"""

import os
from pathlib import Path
import pandas as pd

def check_data_directory():
    """检查数据目录结构和文件"""
    
    print("=" * 60)
    print("数据目录检查 / Data Directory Check")
    print("=" * 60)
    print()
    
    data_dir = Path("data")
    
    if not data_dir.exists():
        print("❌ data 目录不存在！")
        return
    
    # 统计文件
    all_files = list(data_dir.rglob("*"))
    data_files = [f for f in all_files if f.is_file() and f.suffix in ['.parquet', '.csv']]
    
    print(f"📊 数据目录统计:")
    print(f"  - 总文件数: {len([f for f in all_files if f.is_file()])}")
    print(f"  - 数据文件数: {len(data_files)}")
    print()
    
    # 按扩展名分组
    from collections import Counter
    extensions = Counter([f.suffix for f in all_files if f.is_file()])
    
    print(f"📁 文件类型分布:")
    for ext, count in extensions.most_common():
        print(f"  - {ext if ext else '(无扩展名)'}: {count} 个文件")
    print()
    
    # 按年份分组
    years = sorted(set([f.parts[1] for f in data_files if len(f.parts) > 1 and f.parts[1].isdigit()]))
    
    print(f"📅 数据年份范围:")
    if years:
        print(f"  - 从 {years[0]} 到 {years[-1]}")
        print(f"  - 共 {len(years)} 年")
    print()
    
    # 计算总大小
    total_size = sum([f.stat().st_size for f in data_files])
    total_size_mb = total_size / (1024 * 1024)
    total_size_gb = total_size / (1024 * 1024 * 1024)
    
    print(f"💾 数据总大小:")
    print(f"  - {total_size_mb:.2f} MB")
    print(f"  - {total_size_gb:.2f} GB")
    print()
    
    # 检查示例文件
    if data_files:
        print("=" * 60)
        print("示例数据文件检查")
        print("=" * 60)
        print()
        
        # 找一个 parquet 文件
        parquet_files = [f for f in data_files if f.suffix == '.parquet']
        
        if parquet_files:
            sample_file = parquet_files[0]
            print(f"📄 检查文件: {sample_file.relative_to(data_dir)}")
            print(f"   大小: {sample_file.stat().st_size / (1024 * 1024):.2f} MB")
            print()
            
            try:
                # 读取文件
                df = pd.read_parquet(sample_file)
                
                print(f"✅ 文件可以正常读取！")
                print()
                print(f"📊 数据信息:")
                print(f"  - 行数: {len(df):,}")
                print(f"  - 列数: {len(df.columns)}")
                print()
                
                print(f"📋 列名:")
                for col in df.columns:
                    print(f"  - {col} ({df[col].dtype})")
                print()
                
                print(f"🔍 前 5 行数据:")
                print(df.head())
                print()
                
                print(f"📈 数据统计:")
                print(df.describe())
                print()
                
                # 检查时间范围
                if 'timestamp' in df.columns or 'time' in df.columns or 'datetime' in df.columns:
                    time_col = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()][0]
                    print(f"⏰ 时间范围:")
                    print(f"  - 列名: {time_col}")
                    print(f"  - 开始: {df[time_col].min()}")
                    print(f"  - 结束: {df[time_col].max()}")
                    print()
                
                # 检查是否有必需的列
                required_cols = ['price', 'volume']
                optional_cols = ['timestamp', 'time', 'datetime', 'bid', 'ask', 'side']
                
                print(f"✅ 列检查:")
                for col in required_cols:
                    matching = [c for c in df.columns if col.lower() in c.lower()]
                    if matching:
                        print(f"  ✓ {col}: 找到 {matching}")
                    else:
                        print(f"  ✗ {col}: 未找到")
                
                for col in optional_cols:
                    matching = [c for c in df.columns if col.lower() in c.lower()]
                    if matching:
                        print(f"  ✓ {col} (可选): 找到 {matching}")
                
                print()
                
            except Exception as e:
                print(f"❌ 读取文件失败: {e}")
                print()
        
        # 显示更多文件示例
        print("=" * 60)
        print("其他数据文件示例 (前 10 个)")
        print("=" * 60)
        print()
        
        for i, f in enumerate(data_files[:10], 1):
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"{i:2d}. {f.relative_to(data_dir)} ({size_mb:.2f} MB)")
        
        if len(data_files) > 10:
            print(f"    ... 还有 {len(data_files) - 10} 个文件")
        print()
    
    else:
        print("❌ 没有找到数据文件！")
        print()
    
    print("=" * 60)
    print("检查完成！")
    print("=" * 60)


if __name__ == "__main__":
    check_data_directory()

