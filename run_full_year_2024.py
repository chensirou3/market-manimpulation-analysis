# -*- coding: utf-8 -*-
"""
运行 2024 年完整数据分析
Run Full Year 2024 Analysis
"""

import sys
import os

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from run_full_pipeline import run_full_pipeline


if __name__ == "__main__":
    print("\n")
    print("=" * 80)
    print("运行 2024 年完整数据分析")
    print("Run Full Year 2024 Analysis")
    print("=" * 80)
    print()
    print("这将加载 2024 年全年的数据（约 3000 万条 tick）")
    print("预计需要 5-10 分钟，请耐心等待...")
    print()
    
    results = run_full_pipeline(
        start_date='2024-01-01',
        end_date='2024-12-31',
        timeframe='5min',
        save_results=True
    )
    
    if results:
        print()
        print("=" * 80)
        print("2024 年完整分析完成！")
        print("=" * 80)
        print()
        print("结果已保存至: results/bars_with_manipscore_2024-01-01_2024-12-31.csv")
        print()
        print("下一步建议:")
        print("  1. 查看 results/ 目录中的 CSV 文件")
        print("  2. 使用 Jupyter Notebook 进行可视化分析")
        print("  3. 调整参数重新运行")
        print()

