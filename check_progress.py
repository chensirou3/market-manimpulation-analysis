"""
检查处理进度
Check processing progress
"""

from pathlib import Path
import pandas as pd
from datetime import datetime

results_dir = Path('results')

# 获取所有结果文件
csv_files = sorted(results_dir.glob('bars_with_manipscore_*.csv'))

print("=" * 80)
print("处理进度检查")
print("Processing Progress Check")
print("=" * 80)
print()

if not csv_files:
    print("❌ 还没有生成结果文件")
else:
    print(f"✅ 已生成 {len(csv_files)} 个结果文件\n")
    
    # 按年份统计
    years_processed = {}
    for f in csv_files:
        # 从文件名提取年份: bars_with_manipscore_2024-01-01_2024-03-31.csv
        parts = f.stem.split('_')
        if len(parts) >= 3:
            year = parts[2][:4]
            if year not in years_processed:
                years_processed[year] = []
            years_processed[year].append(f.name)
    
    print("📅 按年份统计:")
    for year in sorted(years_processed.keys()):
        files = years_processed[year]
        print(f"  {year}: {len(files)} 个季度")
        for fname in sorted(files):
            print(f"    - {fname}")
    
    print()
    
    # 最新文件
    latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
    latest_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
    
    print(f"📄 最新文件:")
    print(f"  {latest_file.name}")
    print(f"  生成时间: {latest_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  大小: {latest_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # 预计进度
    total_quarters = 43  # 2015-2025
    processed_quarters = len(csv_files)
    progress = processed_quarters / total_quarters * 100
    
    print()
    print(f"📊 总体进度:")
    print(f"  已完成: {processed_quarters}/{total_quarters} 个季度 ({progress:.1f}%)")
    print(f"  剩余: {total_quarters - processed_quarters} 个季度")
    
    # 进度条
    bar_length = 50
    filled = int(bar_length * progress / 100)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f"  [{bar}] {progress:.1f}%")

print()
print("=" * 80)

