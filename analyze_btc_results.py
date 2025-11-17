import pandas as pd
import numpy as np

# Load trades
trades = pd.read_csv('results/BTCUSD_4h_full_dynamic_strength_trades.csv')
trades.columns = ['entry_time', 'exit_time', 'signal_strength', 'entry_price', 'exit_price', 'pnl', 'holding_bars', 'exit_reason']

# Load equity curve
equity = pd.read_csv('results/BTCUSD_4h_full_dynamic_strength_equity.csv')

print("=" * 80)
print("BTCUSD 4H Dynamic Strength Exit - Full Period (2017-2024)")
print("=" * 80)

# Basic statistics
print(f"\n📊 OVERALL STATISTICS")
print(f"{'─' * 80}")
print(f"Total Trades: {len(trades)}")
print(f"Win Rate: {(trades['pnl'] > 0).mean():.2%}")
print(f"Date Range: {trades['entry_time'].min()} to {trades['exit_time'].max()}")

# PnL statistics
print(f"\n💰 PnL STATISTICS")
print(f"{'─' * 80}")
print(f"Mean PnL: {trades['pnl'].mean():.4f} ({trades['pnl'].mean()*100:.2f}%)")
print(f"Median PnL: {trades['pnl'].median():.4f} ({trades['pnl'].median()*100:.2f}%)")
print(f"Std Dev: {trades['pnl'].std():.4f} ({trades['pnl'].std()*100:.2f}%)")
print(f"Min PnL: {trades['pnl'].min():.4f} ({trades['pnl'].min()*100:.2f}%)")
print(f"Max PnL: {trades['pnl'].max():.4f} ({trades['pnl'].max()*100:.2f}%)")

# Winning trades
wins = trades[trades['pnl'] > 0]
print(f"\n✅ WINNING TRADES")
print(f"{'─' * 80}")
print(f"Count: {len(wins)} ({len(wins)/len(trades)*100:.1f}%)")
print(f"Avg Win: {wins['pnl'].mean():.4f} ({wins['pnl'].mean()*100:.2f}%)")
print(f"Max Win: {wins['pnl'].max():.4f} ({wins['pnl'].max()*100:.2f}%)")
print(f"Total Win Amount: {wins['pnl'].sum():.4f} ({wins['pnl'].sum()*100:.2f}%)")

# Losing trades
losses = trades[trades['pnl'] <= 0]
print(f"\n❌ LOSING TRADES")
print(f"{'─' * 80}")
print(f"Count: {len(losses)} ({len(losses)/len(trades)*100:.1f}%)")
print(f"Avg Loss: {losses['pnl'].mean():.4f} ({losses['pnl'].mean()*100:.2f}%)")
print(f"Max Loss: {losses['pnl'].min():.4f} ({losses['pnl'].min()*100:.2f}%)")
print(f"Total Loss Amount: {losses['pnl'].sum():.4f} ({losses['pnl'].sum()*100:.2f}%)")

# Profit factor
profit_factor = wins['pnl'].sum() / abs(losses['pnl'].sum()) if len(losses) > 0 else np.inf
print(f"\n📈 PROFIT FACTOR: {profit_factor:.2f}")

# By signal strength
print(f"\n🎯 BY SIGNAL STRENGTH")
print(f"{'─' * 80}")
for strength in ['strong', 'medium', 'weak']:
    subset = trades[trades['signal_strength'] == strength]
    if len(subset) > 0:
        wr = (subset['pnl'] > 0).mean()
        avg_pnl = subset['pnl'].mean()
        total_pnl = subset['pnl'].sum()
        print(f"{strength.upper():8s}: {len(subset):3d} trades | WR={wr:5.1%} | Avg PnL={avg_pnl*100:6.2f}% | Total={total_pnl*100:7.2f}%")

# By exit reason
print(f"\n🚪 BY EXIT REASON")
print(f"{'─' * 80}")
for reason in trades['exit_reason'].unique():
    subset = trades[trades['exit_reason'] == reason]
    wr = (subset['pnl'] > 0).mean()
    avg_pnl = subset['pnl'].mean()
    print(f"{reason:15s}: {len(subset):3d} trades | WR={wr:5.1%} | Avg PnL={avg_pnl*100:6.2f}%")

# Holding period
print(f"\n⏱️  HOLDING PERIOD")
print(f"{'─' * 80}")
print(f"Avg Holding: {trades['holding_bars'].mean():.1f} bars ({trades['holding_bars'].mean()*4:.1f} hours)")
print(f"Min Holding: {trades['holding_bars'].min()} bars ({trades['holding_bars'].min()*4} hours)")
print(f"Max Holding: {trades['holding_bars'].max()} bars ({trades['holding_bars'].max()*4} hours)")

# Equity curve analysis
print(f"\n📈 EQUITY CURVE ANALYSIS")
print(f"{'─' * 80}")
print(f"Date Range: {equity['timestamp'].min()} to {equity['timestamp'].max()}")
print(f"Total Bars: {len(equity)}")
print(f"Initial Equity: ${equity['equity'].iloc[0]:,.2f}")
print(f"Final Equity: ${equity['equity'].iloc[-1]:,.2f}")
total_return = (equity['equity'].iloc[-1] / equity['equity'].iloc[0] - 1)
print(f"Total Return: {total_return*100:.2f}%")
print(f"Peak Equity: ${equity['equity'].max():,.2f}")
print(f"Trough Equity: ${equity['equity'].min():,.2f}")

# Drawdown analysis
equity['peak'] = equity['equity'].cummax()
equity['dd'] = (equity['equity'] - equity['peak']) / equity['peak']
max_dd = equity['dd'].min()
avg_dd = equity[equity['dd'] < 0]['dd'].mean()
dd_periods = (equity['dd'] < -0.1).sum()

print(f"\n📉 DRAWDOWN ANALYSIS")
print(f"{'─' * 80}")
print(f"Max Drawdown: {max_dd*100:.2f}%")
print(f"Avg Drawdown (when in DD): {avg_dd*100:.2f}%")
print(f"Periods with DD > 10%: {dd_periods} bars ({dd_periods/len(equity)*100:.1f}%)")
print(f"Periods with DD > 20%: {(equity['dd'] < -0.2).sum()} bars ({(equity['dd'] < -0.2).sum()/len(equity)*100:.1f}%)")
print(f"Periods with DD > 30%: {(equity['dd'] < -0.3).sum()} bars ({(equity['dd'] < -0.3).sum()/len(equity)*100:.1f}%)")

# Annualized metrics
years = len(equity) / (365.25 * 6)  # 4H bars per year
ann_return = (1 + total_return) ** (1/years) - 1
returns = equity['equity'].pct_change().dropna()
ann_vol = returns.std() * np.sqrt(365.25 * 6)
sharpe = ann_return / ann_vol if ann_vol > 0 else 0

print(f"\n📊 ANNUALIZED METRICS")
print(f"{'─' * 80}")
print(f"Period: {years:.2f} years")
print(f"Annualized Return: {ann_return*100:.2f}%")
print(f"Annualized Volatility: {ann_vol*100:.2f}%")
print(f"Sharpe Ratio: {sharpe:.2f}")

# Top 10 best trades
print(f"\n🏆 TOP 10 BEST TRADES")
print(f"{'─' * 80}")
top_trades = trades.nlargest(10, 'pnl')[['entry_time', 'signal_strength', 'pnl', 'holding_bars', 'exit_reason']]
for idx, row in top_trades.iterrows():
    print(f"{row['entry_time'][:10]} | {row['signal_strength']:6s} | PnL={row['pnl']*100:6.2f}% | {row['holding_bars']:2.0f} bars | {row['exit_reason']}")

# Top 10 worst trades
print(f"\n💀 TOP 10 WORST TRADES")
print(f"{'─' * 80}")
worst_trades = trades.nsmallest(10, 'pnl')[['entry_time', 'signal_strength', 'pnl', 'holding_bars', 'exit_reason']]
for idx, row in worst_trades.iterrows():
    print(f"{row['entry_time'][:10]} | {row['signal_strength']:6s} | PnL={row['pnl']*100:6.2f}% | {row['holding_bars']:2.0f} bars | {row['exit_reason']}")

print(f"\n{'=' * 80}")

