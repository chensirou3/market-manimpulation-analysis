"""
Detailed Strategy Analysis with 7bp Transaction Cost

Analyze all strategies with realistic 7bp cost and extract detailed metrics:
- Total return and annualized return
- Maximum drawdown
- Trading frequency (trades per year)
- Average holding time
- Win rate and average win/loss
- Sharpe ratio
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from src.strategies.extreme_reversal import ExtremeReversalConfig
from src.strategies.backtest_reversal import run_extreme_reversal_backtest
from src.strategies.trend_features import compute_trend_strength, compute_extreme_trend_thresholds

print("=" * 100)
print("DETAILED STRATEGY ANALYSIS - 7bp Transaction Cost")
print("=" * 100)

def generate_asymmetric_signals(bars, config):
    """Generate asymmetric signals: UP=continuation, DOWN=reversal"""
    signals = pd.DataFrame(index=bars.index)
    signals['signal'] = 0
    
    bars = compute_trend_strength(bars, L_past=config.L_past, vol_window=config.vol_window)
    thresholds = compute_extreme_trend_thresholds(bars, quantile=config.q_extreme_trend)
    threshold = thresholds['threshold']
    
    extreme_up = bars['TS'] > threshold
    extreme_down = bars['TS'] < -threshold
    high_manip = bars['ManipScore'] > bars['ManipScore'].quantile(config.q_manip)
    
    signals.loc[extreme_up & high_manip, 'signal'] = 1
    signals.loc[extreme_down & high_manip, 'signal'] = 1
    signals['signal'] = signals['signal'].shift(1).fillna(0)
    
    return signals

def calculate_detailed_metrics(result, bars, timeframe):
    """Calculate detailed metrics from backtest result."""
    trades = result.trades
    stats = result.stats
    
    if len(trades) == 0:
        return None
    
    # Basic metrics
    total_return = stats.get('total_return', 0) * 100
    sharpe = stats.get('sharpe_ratio', 0)
    max_dd = stats.get('max_drawdown', 0) * 100
    win_rate = stats.get('win_rate', 0) * 100
    
    # Time period
    start_date = bars.index[0]
    end_date = bars.index[-1]
    years = (end_date - start_date).days / 365.25
    
    # Annualized return
    if total_return > -99:
        ann_return = ((1 + total_return/100) ** (1/years) - 1) * 100
    else:
        ann_return = -100
    
    # Trading frequency
    num_trades = len(trades)
    trades_per_year = num_trades / years
    
    # Average holding time
    holding_times = []
    for trade in trades:
        if trade.exit_time is not None and trade.entry_time is not None:
            # Handle both datetime and integer (bar count) cases
            if isinstance(trade.exit_time, (int, np.integer)):
                # If times are stored as bar counts
                holding_time = trade.exit_time - trade.entry_time
                holding_times.append(holding_time)
            else:
                # If times are datetime objects
                holding_time = (trade.exit_time - trade.entry_time).total_seconds() / 3600  # hours
                holding_times.append(holding_time)
    
    # Calculate average holding time
    if holding_times:
        avg_holding_value = np.mean(holding_times)
        # Check if we're dealing with hours or bar counts
        if trades and isinstance(trades[0].exit_time, (int, np.integer)):
            # Bar counts - convert to hours based on timeframe
            timeframe_hours = {
                '5min': 5/60, '15min': 15/60, '30min': 30/60,
                '60min': 1, '4h': 4, '1d': 24
            }
            hours_per_bar = timeframe_hours.get(timeframe, 1)
            avg_holding_hours = avg_holding_value * hours_per_bar
        else:
            avg_holding_hours = avg_holding_value
        avg_holding_days = avg_holding_hours / 24
    else:
        avg_holding_hours = 0
        avg_holding_days = 0
    
    # Win/Loss analysis
    winning_trades = [t for t in trades if t.pnl and t.pnl > 0]
    losing_trades = [t for t in trades if t.pnl and t.pnl <= 0]
    
    avg_win = np.mean([t.pnl_pct * 100 for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t.pnl_pct * 100 for t in losing_trades]) if losing_trades else 0
    
    # Profit factor
    total_wins = sum([t.pnl for t in winning_trades]) if winning_trades else 0
    total_losses = abs(sum([t.pnl for t in losing_trades])) if losing_trades else 0
    profit_factor = total_wins / total_losses if total_losses > 0 else 0
    
    return {
        'Start_Date': start_date.strftime('%Y-%m-%d'),
        'End_Date': end_date.strftime('%Y-%m-%d'),
        'Years': round(years, 2),
        'Total_Return_Pct': round(total_return, 2),
        'Ann_Return_Pct': round(ann_return, 2),
        'Sharpe': round(sharpe, 2),
        'Max_DD_Pct': round(max_dd, 2),
        'Num_Trades': num_trades,
        'Trades_Per_Year': round(trades_per_year, 1),
        'Avg_Holding_Hours': round(avg_holding_hours, 1),
        'Avg_Holding_Days': round(avg_holding_days, 2),
        'Win_Rate_Pct': round(win_rate, 1),
        'Avg_Win_Pct': round(avg_win, 3),
        'Avg_Loss_Pct': round(avg_loss, 3),
        'Profit_Factor': round(profit_factor, 2),
    }

def analyze_strategy(asset, timeframe, use_sl_tp, cost=0.0007):
    """Analyze a specific strategy with detailed metrics."""
    # Determine file path
    if asset == 'XAUUSD':
        bars_path = f'results/bars_{timeframe}_with_manipscore_full.csv'
    else:
        bars_path = f'results/bars_{timeframe}_{asset.lower()}_full_with_manipscore.csv'
    
    if not Path(bars_path).exists():
        print(f"  File not found: {bars_path}")
        return None
    
    bars = pd.read_csv(bars_path, index_col=0, parse_dates=True)
    
    config = ExtremeReversalConfig(
        bar_size=timeframe,
        L_past=5,
        vol_window=20,
        q_extreme_trend=0.9,
        q_manip=0.9,
        holding_horizon=5,
        atr_window=10,
        sl_atr_mult=0.5 if use_sl_tp else 999.0,
        tp_atr_mult=0.8 if use_sl_tp else 999.0,
        cost_per_trade=cost
    )
    
    signals = generate_asymmetric_signals(bars, config)
    bars['exec_signal'] = signals['signal']
    result = run_extreme_reversal_backtest(bars, bars['exec_signal'], config, initial_capital=10000)
    
    metrics = calculate_detailed_metrics(result, bars, timeframe)
    
    if metrics:
        metrics['Asset'] = asset
        metrics['Timeframe'] = timeframe
        metrics['SL_TP'] = 'Yes' if use_sl_tp else 'No'
        metrics['Cost_BP'] = cost * 10000
    
    return metrics, result

# Define all strategies to test
strategies = [
    # BTC strategies
    {'asset': 'BTC', 'timeframe': '4h', 'use_sl_tp': False, 'name': 'BTC 4h Pure'},
    {'asset': 'BTC', 'timeframe': '4h', 'use_sl_tp': True, 'name': 'BTC 4h+SL/TP'},
    {'asset': 'BTC', 'timeframe': '60min', 'use_sl_tp': False, 'name': 'BTC 60min Pure'},
    {'asset': 'BTC', 'timeframe': '60min', 'use_sl_tp': True, 'name': 'BTC 60min+SL/TP'},
    {'asset': 'BTC', 'timeframe': '15min', 'use_sl_tp': True, 'name': 'BTC 15min+SL/TP'},
    {'asset': 'BTC', 'timeframe': '5min', 'use_sl_tp': True, 'name': 'BTC 5min+SL/TP'},
    
    # ETH strategies
    {'asset': 'ETH', 'timeframe': '30min', 'use_sl_tp': True, 'name': 'ETH 30min+SL/TP'},
    {'asset': 'ETH', 'timeframe': '60min', 'use_sl_tp': False, 'name': 'ETH 60min Pure'},
    {'asset': 'ETH', 'timeframe': '60min', 'use_sl_tp': True, 'name': 'ETH 60min+SL/TP'},
    {'asset': 'ETH', 'timeframe': '15min', 'use_sl_tp': True, 'name': 'ETH 15min+SL/TP'},
    {'asset': 'ETH', 'timeframe': '5min', 'use_sl_tp': True, 'name': 'ETH 5min+SL/TP'},
    
    # XAUUSD strategies
    {'asset': 'XAUUSD', 'timeframe': '4h', 'use_sl_tp': False, 'name': 'XAUUSD 4h Pure'},
    {'asset': 'XAUUSD', 'timeframe': '4h', 'use_sl_tp': True, 'name': 'XAUUSD 4h+SL/TP'},
]

all_metrics = []

for strat in strategies:
    print(f"\n{'='*100}")
    print(f"Analyzing: {strat['name']}")
    print(f"{'='*100}")
    
    try:
        metrics, result = analyze_strategy(
            strat['asset'],
            strat['timeframe'],
            strat['use_sl_tp'],
            cost=0.0007  # 7bp
        )
        
        if metrics:
            all_metrics.append(metrics)
            
            # Print detailed results
            print(f"\nPerformance Metrics:")
            print(f"  Period: {metrics['Start_Date']} to {metrics['End_Date']} ({metrics['Years']} years)")
            print(f"  Total Return: {metrics['Total_Return_Pct']:.2f}%")
            print(f"  Annualized Return: {metrics['Ann_Return_Pct']:.2f}%")
            print(f"  Sharpe Ratio: {metrics['Sharpe']:.2f}")
            print(f"  Max Drawdown: {metrics['Max_DD_Pct']:.2f}%")

            print(f"\nTrading Activity:")
            print(f"  Total Trades: {metrics['Num_Trades']}")
            print(f"  Trades per Year: {metrics['Trades_Per_Year']:.1f}")
            print(f"  Avg Holding Time: {metrics['Avg_Holding_Days']:.2f} days ({metrics['Avg_Holding_Hours']:.1f} hours)")

            print(f"\nWin/Loss Analysis:")
            print(f"  Win Rate: {metrics['Win_Rate_Pct']:.1f}%")
            print(f"  Avg Win: {metrics['Avg_Win_Pct']:.3f}%")
            print(f"  Avg Loss: {metrics['Avg_Loss_Pct']:.3f}%")
            print(f"  Profit Factor: {metrics['Profit_Factor']:.2f}")
    
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()

# Save results
print("\n" + "=" * 100)
print("Saving Results")
print("=" * 100)

df = pd.DataFrame(all_metrics)
output_path = 'results/detailed_strategy_analysis_7bp.csv'
df.to_csv(output_path, index=False)
print(f"Saved: {output_path}")

# Print summary table
print("\n" + "=" * 100)
print("SUMMARY TABLE - Sorted by Annualized Return")
print("=" * 100)

df_sorted = df.sort_values('Ann_Return_Pct', ascending=False)
print(df_sorted[['Asset', 'Timeframe', 'SL_TP', 'Ann_Return_Pct', 'Sharpe', 'Max_DD_Pct', 
                 'Trades_Per_Year', 'Avg_Holding_Days', 'Win_Rate_Pct']].to_string(index=False))

print("\n" + "=" * 100)
print("Analysis Complete!")
print("=" * 100)

