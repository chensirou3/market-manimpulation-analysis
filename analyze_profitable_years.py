import pandas as pd
import numpy as np

# Load trades
trades = pd.read_csv('results/BTCUSD_4h_full_dynamic_strength_trades.csv')
trades.columns = ['entry_time', 'exit_time', 'signal_strength', 'entry_price', 'exit_price', 'pnl', 'holding_bars', 'exit_reason']
trades['entry_time'] = pd.to_datetime(trades['entry_time'])
trades['exit_time'] = pd.to_datetime(trades['exit_time'])
trades['year'] = trades['entry_time'].dt.year

print("=" * 100)
print("BTCUSD 4H Dynamic Strength - PROFITABLE YEARS DEEP DIVE")
print("=" * 100)

# Identify profitable years
yearly_pnl = trades.groupby('year')['pnl'].sum()
profitable_years = yearly_pnl[yearly_pnl > 0].index.tolist()
losing_years = yearly_pnl[yearly_pnl <= 0].index.tolist()

print(f"\n📊 OVERVIEW")
print(f"{'─' * 100}")
print(f"Profitable Years: {len(profitable_years)} - {profitable_years}")
print(f"Losing Years: {len(losing_years)} - {losing_years}")
print(f"Win Rate (Years): {len(profitable_years)/(len(profitable_years)+len(losing_years))*100:.1f}%")

# Analyze each profitable year in detail
for year in profitable_years:
    year_trades = trades[trades['year'] == year]
    wins = year_trades[year_trades['pnl'] > 0]
    losses = year_trades[year_trades['pnl'] <= 0]
    
    print(f"\n{'=' * 100}")
    print(f"📅 {year} - PROFITABLE YEAR (+{year_trades['pnl'].sum()*100:.2f}%)")
    print(f"{'=' * 100}")
    
    # Overall stats
    print(f"\n📊 OVERALL STATISTICS")
    print(f"{'─' * 100}")
    print(f"Total Trades: {len(year_trades)}")
    print(f"Win Rate: {len(wins)/len(year_trades)*100:.1f}% ({len(wins)} wins / {len(losses)} losses)")
    print(f"Total PnL: {year_trades['pnl'].sum()*100:.2f}%")
    print(f"Avg PnL per Trade: {year_trades['pnl'].mean()*100:.2f}%")
    print(f"Median PnL: {year_trades['pnl'].median()*100:.2f}%")
    print(f"Best Trade: {year_trades['pnl'].max()*100:.2f}%")
    print(f"Worst Trade: {year_trades['pnl'].min()*100:.2f}%")
    
    # Win/Loss breakdown
    print(f"\n✅ WINNING TRADES")
    print(f"{'─' * 100}")
    print(f"Count: {len(wins)}")
    print(f"Avg Win: {wins['pnl'].mean()*100:.2f}%")
    print(f"Total Win Amount: {wins['pnl'].sum()*100:.2f}%")
    print(f"Largest Win: {wins['pnl'].max()*100:.2f}%")
    
    print(f"\n❌ LOSING TRADES")
    print(f"{'─' * 100}")
    print(f"Count: {len(losses)}")
    if len(losses) > 0:
        print(f"Avg Loss: {losses['pnl'].mean()*100:.2f}%")
        print(f"Total Loss Amount: {losses['pnl'].sum()*100:.2f}%")
        print(f"Largest Loss: {losses['pnl'].min()*100:.2f}%")
        profit_factor = wins['pnl'].sum() / abs(losses['pnl'].sum())
        print(f"Profit Factor: {profit_factor:.2f}")
    else:
        print(f"No losing trades!")
    
    # By signal strength
    print(f"\n🎯 BY SIGNAL STRENGTH")
    print(f"{'─' * 100}")
    for strength in ['strong', 'medium', 'weak']:
        subset = year_trades[year_trades['signal_strength'] == strength]
        if len(subset) > 0:
            wr = (subset['pnl'] > 0).mean()
            avg_pnl = subset['pnl'].mean()
            total_pnl = subset['pnl'].sum()
            best = subset['pnl'].max()
            worst = subset['pnl'].min()
            print(f"{strength.upper():8s}: {len(subset):2d} trades | WR={wr*100:5.1f}% | Avg={avg_pnl*100:6.2f}% | Total={total_pnl*100:7.2f}% | Best={best*100:6.2f}% | Worst={worst*100:7.2f}%")
    
    # Monthly breakdown
    print(f"\n📆 MONTHLY BREAKDOWN")
    print(f"{'─' * 100}")
    year_trades['month'] = year_trades['entry_time'].dt.month
    monthly = year_trades.groupby('month').agg({
        'pnl': ['count', 'sum', 'mean']
    }).round(4)
    
    for month in range(1, 13):
        month_data = year_trades[year_trades['month'] == month]
        if len(month_data) > 0:
            month_pnl = month_data['pnl'].sum()
            month_trades = len(month_data)
            month_wr = (month_data['pnl'] > 0).mean()
            print(f"Month {month:2d}: {month_trades:2d} trades | WR={month_wr*100:5.1f}% | Total PnL={month_pnl*100:7.2f}%")
    
    # Top 5 trades
    print(f"\n🏆 TOP 5 TRADES")
    print(f"{'─' * 100}")
    top5 = year_trades.nlargest(5, 'pnl')
    for idx, row in top5.iterrows():
        print(f"{row['entry_time'].strftime('%Y-%m-%d')} | {row['signal_strength']:6s} | Entry=${row['entry_price']:8.2f} | Exit=${row['exit_price']:8.2f} | PnL={row['pnl']*100:6.2f}%")
    
    # Worst 3 trades
    if len(losses) > 0:
        print(f"\n💀 WORST 3 TRADES")
        print(f"{'─' * 100}")
        worst3 = year_trades.nsmallest(min(3, len(losses)), 'pnl')
        for idx, row in worst3.iterrows():
            print(f"{row['entry_time'].strftime('%Y-%m-%d')} | {row['signal_strength']:6s} | Entry=${row['entry_price']:8.2f} | Exit=${row['exit_price']:8.2f} | PnL={row['pnl']*100:6.2f}%")

# Summary comparison
print(f"\n{'=' * 100}")
print(f"PROFITABLE YEARS COMPARISON")
print(f"{'=' * 100}")

summary_data = []
for year in profitable_years:
    year_trades = trades[trades['year'] == year]
    wins = year_trades[year_trades['pnl'] > 0]
    losses = year_trades[year_trades['pnl'] <= 0]
    
    summary_data.append({
        'Year': year,
        'Trades': len(year_trades),
        'Win_Rate': len(wins)/len(year_trades),
        'Total_PnL': year_trades['pnl'].sum(),
        'Avg_PnL': year_trades['pnl'].mean(),
        'Best': year_trades['pnl'].max(),
        'Worst': year_trades['pnl'].min(),
        'Profit_Factor': wins['pnl'].sum() / abs(losses['pnl'].sum()) if len(losses) > 0 else np.inf
    })

df_summary = pd.DataFrame(summary_data)
print(f"\n{'Year':<6} {'Trades':<8} {'WinRate':<10} {'Total PnL':<12} {'Avg PnL':<10} {'Best':<10} {'Worst':<10} {'PF':<8}")
print(f"{'─' * 100}")
for _, row in df_summary.iterrows():
    pf_str = f"{row['Profit_Factor']:.2f}" if row['Profit_Factor'] != np.inf else "∞"
    print(f"{row['Year']:<6.0f} {row['Trades']:<8.0f} {row['Win_Rate']*100:<9.1f}% {row['Total_PnL']*100:<11.2f}% {row['Avg_PnL']*100:<9.2f}% {row['Best']*100:<9.2f}% {row['Worst']*100:<9.2f}% {pf_str:<8s}")

print(f"\n{'=' * 100}")
print(f"KEY INSIGHTS")
print(f"{'=' * 100}")
print(f"Best Performing Year: {df_summary.loc[df_summary['Total_PnL'].idxmax(), 'Year']:.0f} with {df_summary['Total_PnL'].max()*100:.2f}% total PnL")
print(f"Highest Win Rate: {df_summary.loc[df_summary['Win_Rate'].idxmax(), 'Year']:.0f} with {df_summary['Win_Rate'].max()*100:.1f}%")
print(f"Best Avg PnL: {df_summary.loc[df_summary['Avg_PnL'].idxmax(), 'Year']:.0f} with {df_summary['Avg_PnL'].max()*100:.2f}% per trade")
print(f"Most Trades: {df_summary.loc[df_summary['Trades'].idxmax(), 'Year']:.0f} with {df_summary['Trades'].max():.0f} trades")
print(f"\nAverage across profitable years:")
print(f"  Avg Win Rate: {df_summary['Win_Rate'].mean()*100:.1f}%")
print(f"  Avg Total PnL: {df_summary['Total_PnL'].mean()*100:.2f}%")
print(f"  Avg Trades per Year: {df_summary['Trades'].mean():.1f}")

