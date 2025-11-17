import pandas as pd
import numpy as np

# Load trades
trades = pd.read_csv('results/BTCUSD_4h_full_dynamic_strength_trades.csv')
trades.columns = ['entry_time', 'exit_time', 'signal_strength', 'entry_price', 'exit_price', 'pnl', 'holding_bars', 'exit_reason']
trades['entry_time'] = pd.to_datetime(trades['entry_time'])
trades['exit_time'] = pd.to_datetime(trades['exit_time'])
trades['year'] = trades['entry_time'].dt.year

print("=" * 80)
print("BTCUSD 4H Dynamic Strength - Yearly Performance Breakdown")
print("=" * 80)

# Group by year
for year in sorted(trades['year'].unique()):
    year_trades = trades[trades['year'] == year]
    
    wins = year_trades[year_trades['pnl'] > 0]
    losses = year_trades[year_trades['pnl'] <= 0]
    
    print(f"\n📅 {year}")
    print(f"{'─' * 80}")
    print(f"Trades: {len(year_trades):3d} | Win Rate: {(len(wins)/len(year_trades)*100):5.1f}% | Total PnL: {year_trades['pnl'].sum()*100:7.2f}%")
    print(f"  Avg PnL: {year_trades['pnl'].mean()*100:6.2f}% | Best: {year_trades['pnl'].max()*100:6.2f}% | Worst: {year_trades['pnl'].min()*100:7.2f}%")
    
    # By strength
    for strength in ['strong', 'medium', 'weak']:
        subset = year_trades[year_trades['signal_strength'] == strength]
        if len(subset) > 0:
            wr = (subset['pnl'] > 0).mean() * 100
            avg_pnl = subset['pnl'].mean() * 100
            total_pnl = subset['pnl'].sum() * 100
            print(f"  {strength:6s}: {len(subset):2d} trades | WR={wr:5.1f}% | Avg={avg_pnl:6.2f}% | Total={total_pnl:7.2f}%")

# Summary statistics
print(f"\n{'=' * 80}")
print(f"SUMMARY BY YEAR")
print(f"{'=' * 80}")

yearly_summary = []
for year in sorted(trades['year'].unique()):
    year_trades = trades[trades['year'] == year]
    yearly_summary.append({
        'Year': year,
        'Trades': len(year_trades),
        'Win_Rate': (year_trades['pnl'] > 0).mean(),
        'Total_PnL': year_trades['pnl'].sum(),
        'Avg_PnL': year_trades['pnl'].mean(),
        'Best': year_trades['pnl'].max(),
        'Worst': year_trades['pnl'].min()
    })

df_summary = pd.DataFrame(yearly_summary)
print(f"\n{'Year':<6} {'Trades':<8} {'WinRate':<10} {'Total PnL':<12} {'Avg PnL':<10} {'Best':<10} {'Worst':<10}")
print(f"{'─' * 80}")
for _, row in df_summary.iterrows():
    print(f"{row['Year']:<6.0f} {row['Trades']:<8.0f} {row['Win_Rate']*100:<9.1f}% {row['Total_PnL']*100:<11.2f}% {row['Avg_PnL']*100:<9.2f}% {row['Best']*100:<9.2f}% {row['Worst']*100:<9.2f}%")

print(f"\n{'=' * 80}")
print(f"Best Year: {df_summary.loc[df_summary['Total_PnL'].idxmax(), 'Year']:.0f} with {df_summary['Total_PnL'].max()*100:.2f}% total PnL")
print(f"Worst Year: {df_summary.loc[df_summary['Total_PnL'].idxmin(), 'Year']:.0f} with {df_summary['Total_PnL'].min()*100:.2f}% total PnL")
print(f"Most Trades: {df_summary.loc[df_summary['Trades'].idxmax(), 'Year']:.0f} with {df_summary['Trades'].max():.0f} trades")
print(f"Highest Win Rate: {df_summary.loc[df_summary['Win_Rate'].idxmax(), 'Year']:.0f} with {df_summary['Win_Rate'].max()*100:.1f}%")

