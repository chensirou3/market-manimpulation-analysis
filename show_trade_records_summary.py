"""
Show summary of all trade path analysis records
"""

import pandas as pd
import os

files = {
    '5min': 'xauusd_5min_trade_path_analysis.csv',
    '15min': 'xauusd_15min_trade_path_analysis.csv',
    '30min': 'xauusd_30min_trade_path_analysis.csv',
    '60min': 'xauusd_60min_trade_path_analysis.csv',
    '4H': 'xauusd_4h_trade_path_analysis.csv',
    '1D': 'xauusd_1d_trade_path_analysis.csv'
}

print('='*80)
print('所有时间周期的交易记录汇总')
print('='*80)
print()

total = 0
for tf, fname in files.items():
    fpath = os.path.join('results', fname)
    if os.path.exists(fpath):
        df = pd.read_csv(fpath)
        n = len(df)
        total += n
        size_mb = os.path.getsize(fpath) / 1024 / 1024
        
        # Count exit reasons
        exit_reasons = df['exit_reason'].value_counts()
        
        print(f'{tf:8s}: {n:5d} 笔交易, 文件大小: {size_mb:.2f} MB')
        print(f'         退出原因: ', end='')
        for reason, count in exit_reasons.items():
            print(f'{reason}={count} ({count/n*100:.1f}%), ', end='')
        print()
        print()

print('='*80)
print(f'总计: {total:,} 笔交易记录')
print('='*80)
print()

# Show detailed info for 4H
print('='*80)
print('4H周期详细信息（最佳周期）')
print('='*80)
print()

df_4h = pd.read_csv('results/xauusd_4h_trade_path_analysis.csv')
print(f'总交易数: {len(df_4h)}')
print()

print('列名:')
for i, col in enumerate(df_4h.columns, 1):
    print(f'  {i:2d}. {col}')
print()

print('数据说明:')
print('  - entry_time: 入场时间')
print('  - exit_time: 出场时间')
print('  - direction: 方向（1=做多）')
print('  - entry_price: 入场价格')
print('  - exit_price: 出场价格')
print('  - holding_bars: 持仓K线数')
print('  - pnl_final: 最终收益率')
print('  - mfe: 最大浮盈（Maximum Favorable Excursion）')
print('  - mae: 最大浮亏（Maximum Adverse Excursion）')
print('  - mfe_atr: MFE的ATR倍数')
print('  - mae_atr: MAE的ATR倍数')
print('  - t_mfe: 达到MFE的K线索引')
print('  - exit_reason: 退出原因')
print()

print('前5笔交易示例:')
print(df_4h[['entry_time', 'exit_time', 'holding_bars', 'pnl_final', 'mfe', 't_mfe', 'exit_reason']].head(5).to_string(index=False))
print()

print('统计信息:')
print(df_4h[['holding_bars', 'pnl_final', 'mfe', 'mae', 't_mfe']].describe().to_string())
print()

# Show best and worst trades
print('='*80)
print('最佳和最差交易（4H周期）')
print('='*80)
print()

print('最佳5笔交易（按pnl_final排序）:')
best_trades = df_4h.nlargest(5, 'pnl_final')[['entry_time', 'exit_time', 'holding_bars', 'pnl_final', 'mfe', 't_mfe']]
print(best_trades.to_string(index=False))
print()

print('最差5笔交易（按pnl_final排序）:')
worst_trades = df_4h.nsmallest(5, 'pnl_final')[['entry_time', 'exit_time', 'holding_bars', 'pnl_final', 'mfe', 't_mfe']]
print(worst_trades.to_string(index=False))
print()

print('='*80)
print('所有交易记录都已保存在 results/ 目录下')
print('可以使用 pandas 读取CSV文件进行进一步分析')
print('='*80)

