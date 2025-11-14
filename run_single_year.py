# -*- coding: utf-8 -*-
"""
运行单个年份数据分析
Run analysis on a single year
"""

import sys

# UTF-8 encoding setup for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from run_full_pipeline import run_full_pipeline

def main():
    """运行单个年份的数据分析"""
    
    # 从命令行参数获取年份
    if len(sys.argv) < 2:
        print("用法: python run_single_year.py <year>")
        print("例如: python run_single_year.py 2015")
        sys.exit(1)
    
    year = int(sys.argv[1])
    
    print(f"开始处理 {year} 年数据...")
    
    # 定义日期范围
    start_date = f"{year}-01-01"
    
    # 2025年只到9月
    if year == 2025:
        end_date = f"{year}-09-30"
    else:
        end_date = f"{year}-12-31"
    
    # 运行流程
    results = run_full_pipeline(
        start_date=start_date,
        end_date=end_date,
        timeframe='5min',
        save_results=True
    )
    
    print(f"\n✅ {year} 年处理完成！")
    print(f"Tick 数据: {results.get('n_ticks', 0):,} 条")
    print(f"K 线数据: {results.get('n_bars', 0):,} 根")
    print(f"高操纵分数: {results.get('n_high_manip', 0):,} 个")

if __name__ == "__main__":
    main()

