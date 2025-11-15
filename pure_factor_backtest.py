"""
Pure Factor Backtest - No Stop Loss / Take Profit

Test the raw predictive power of the factor without any risk management.

Compare:
1. Reversal strategy (current)
2. Continuation strategy (new)
3. Asymmetric strategy (UP=continuation, DOWN=reversal)

All with FIXED holding period, NO SL/TP.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from src.strategies import compute_trend_strength, compute_extreme_trend_thresholds

def load_bars(bar_size):
    """Load bars for a specific timeframe"""
    results_dir = Path('results')
    files = sorted(results_dir.glob(f'bars_{bar_size}_with_manipscore_*.csv'))
    
    dfs = []
    for file in files:
        df = pd.read_csv(file, index_col=0, parse_dates=True)
        dfs.append(df)
    
    bars = pd.concat(dfs, axis=0).sort_index()
    return bars


def generate_pure_signals(bars, strategy='reversal', holding_period=5):
    """
    Generate signals without any stop-loss or take-profit.
    
    Args:
        bars: DataFrame with ManipScore
        strategy: 'reversal', 'continuation', or 'asymmetric'
        holding_period: Fixed holding period in bars
    
    Returns:
        DataFrame with signals and returns
    """
    bars = bars.copy()
    
    # Compute trend features
    bars = compute_trend_strength(bars, L_past=5, vol_window=20)
    
    # Compute thresholds
    thresholds = compute_extreme_trend_thresholds(
        bars,
        quantile=0.90,
        use_normalized=True,
        min_abs_R_past=0.003
    )
    
    # Identify extreme trends
    threshold_val = thresholds['threshold']
    extreme_up = (bars['R_past'] > 0) & (bars['abs_TS'] >= threshold_val)
    extreme_down = (bars['R_past'] < 0) & (bars['abs_TS'] >= threshold_val)
    
    # Apply minimum absolute R_past filter
    if thresholds['min_abs_R_past'] is not None:
        min_R = thresholds['min_abs_R_past']
        extreme_up = extreme_up & (bars['abs_R_past'] >= min_R)
        extreme_down = extreme_down & (bars['abs_R_past'] >= min_R)
    
    # High ManipScore
    manip_threshold = bars['ManipScore'].quantile(0.90)
    high_manip = bars['ManipScore'] >= manip_threshold
    
    # Generate signals based on strategy
    bars['raw_signal'] = 0
    
    if strategy == 'reversal':
        # Extreme UP + high manip → SHORT (-1)
        # Extreme DOWN + high manip → LONG (+1)
        bars.loc[extreme_up & high_manip, 'raw_signal'] = -1
        bars.loc[extreme_down & high_manip, 'raw_signal'] = 1
        
    elif strategy == 'continuation':
        # Extreme UP + high manip → LONG (+1)
        # Extreme DOWN + high manip → SHORT (-1)
        bars.loc[extreme_up & high_manip, 'raw_signal'] = 1
        bars.loc[extreme_down & high_manip, 'raw_signal'] = -1
        
    elif strategy == 'asymmetric':
        # Extreme UP + high manip → LONG (+1, follow trend)
        # Extreme DOWN + high manip → LONG (+1, reversal/bounce)
        bars.loc[extreme_up & high_manip, 'raw_signal'] = 1
        bars.loc[extreme_down & high_manip, 'raw_signal'] = 1
    
    # Shift signal to avoid look-ahead bias
    bars['signal'] = bars['raw_signal'].shift(1).fillna(0)
    
    # Compute forward returns for holding period
    bars['forward_return'] = bars['returns'].shift(-1).rolling(holding_period).sum().shift(-holding_period+1)
    
    # Compute strategy returns
    bars['strategy_return'] = bars['signal'] * bars['forward_return']
    
    return bars


def compute_pure_performance(bars):
    """Compute performance metrics without SL/TP"""
    
    # Filter to trades only
    trades = bars[bars['signal'] != 0].copy()
    
    if len(trades) == 0:
        return None
    
    # Basic stats
    n_trades = len(trades)
    n_long = (trades['signal'] > 0).sum()
    n_short = (trades['signal'] < 0).sum()
    
    # Returns
    total_return = trades['strategy_return'].sum()
    avg_return = trades['strategy_return'].mean()
    std_return = trades['strategy_return'].std()
    
    # Win rate
    winners = trades[trades['strategy_return'] > 0]
    losers = trades[trades['strategy_return'] < 0]
    
    n_winners = len(winners)
    n_losers = len(losers)
    win_rate = n_winners / n_trades if n_trades > 0 else 0
    
    avg_winner = winners['strategy_return'].mean() if len(winners) > 0 else 0
    avg_loser = losers['strategy_return'].mean() if len(losers) > 0 else 0
    
    # Sharpe (annualized)
    # Assuming 252 trading days, bars per day depends on timeframe
    sharpe = (avg_return / std_return) * np.sqrt(n_trades) if std_return > 0 else 0
    
    return {
        'n_trades': n_trades,
        'n_long': n_long,
        'n_short': n_short,
        'total_return': total_return,
        'avg_return': avg_return,
        'std_return': std_return,
        'win_rate': win_rate,
        'n_winners': n_winners,
        'n_losers': n_losers,
        'avg_winner': avg_winner,
        'avg_loser': avg_loser,
        'sharpe': sharpe,
    }


def main():
    print("="*80)
    print("PURE FACTOR BACKTEST - No Stop Loss / Take Profit")
    print("="*80)
    print()
    
    strategies = ['reversal', 'continuation', 'asymmetric']
    bar_sizes = ['5min', '30min']
    holding_period = 5
    
    all_results = []
    
    for bar_size in bar_sizes:
        print(f"\n{'='*80}")
        print(f"Testing {bar_size}")
        print(f"{'='*80}\n")
        
        # Load data
        print(f"Loading {bar_size} data...")
        bars = load_bars(bar_size)
        print(f"Loaded {len(bars):,} bars")
        print()
        
        for strategy in strategies:
            print(f"  Strategy: {strategy}")
            
            # Generate signals
            bars_with_signals = generate_pure_signals(bars, strategy, holding_period)
            
            # Compute performance
            perf = compute_pure_performance(bars_with_signals)
            
            if perf is None:
                print(f"    No trades generated")
                continue
            
            print(f"    Trades: {perf['n_trades']:,} (Long: {perf['n_long']}, Short: {perf['n_short']})")
            print(f"    Total return: {perf['total_return']*100:.2f}%")
            print(f"    Avg return per trade: {perf['avg_return']*10000:.2f} bps")
            print(f"    Win rate: {perf['win_rate']*100:.1f}%")
            print(f"    Avg winner: {perf['avg_winner']*10000:.2f} bps")
            print(f"    Avg loser: {perf['avg_loser']*10000:.2f} bps")
            print(f"    Sharpe: {perf['sharpe']:.2f}")
            print()
            
            # Save results
            all_results.append({
                'bar_size': bar_size,
                'strategy': strategy,
                **perf
            })
    
    # Save to CSV
    df_results = pd.DataFrame(all_results)
    df_results.to_csv('results/pure_factor_performance.csv', index=False)
    print(f"\n✅ Saved: results/pure_factor_performance.csv")
    
    # Print comparison
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    print()
    
    for bar_size in bar_sizes:
        print(f"\n{bar_size.upper()}:")
        print(f"{'Strategy':<15} {'Trades':<10} {'Avg Return':<15} {'Win Rate':<12} {'Sharpe':<10}")
        print("-"*80)
        
        df_bs = df_results[df_results['bar_size'] == bar_size]
        for _, row in df_bs.iterrows():
            print(f"{row['strategy']:<15} {row['n_trades']:<10} {row['avg_return']*10000:>8.2f} bps   {row['win_rate']*100:>6.1f}%     {row['sharpe']:>6.2f}")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()

