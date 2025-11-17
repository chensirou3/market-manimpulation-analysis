"""
Create complete strategy evolution table from all historical results.

This script consolidates all strategy iterations from the earliest to the latest,
showing the progression of the market manipulation detection strategy.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Project root
project_root = Path(__file__).parent

def load_all_results():
    """Load all historical results and combine them."""
    
    results = []
    
    # ========================================
    # Phase 1: Original Pure Factor Strategy (XAUUSD only, 2015-2025)
    # ========================================
    # From asymmetric_pure_results.csv
    try:
        df_pure = pd.read_csv(project_root / "results/asymmetric_pure_results.csv")
        for _, row in df_pure.iterrows():
            results.append({
                'Phase': 'Phase 1',
                'Strategy': 'Pure Factor (Asymmetric)',
                'Symbol': 'XAUUSD',
                'Timeframe': row['bar_size'],
                'Period': '2015-2025 (11yr)',
                'Exit Rule': 'Wide SL only',
                'Total Return (%)': row['total_return'] * 100,
                'Sharpe': row['sharpe'],
                'Win Rate (%)': row['win_rate'] * 100,
                'Num Trades': row['n_trades'],
                'Avg PnL/Trade (%)': row['avg_return'] * 100,
                'Max Drawdown (%)': np.nan,
                'Notes': 'Original XAUUSD strategy'
            })
    except Exception as e:
        print(f"Warning: Could not load asymmetric_pure_results.csv: {e}")
    
    # ========================================
    # Phase 2: Extended to BTC/ETH (2017-2024)
    # ========================================
    # From all_assets_complete_comparison.csv
    try:
        df_all = pd.read_csv(project_root / "results/all_assets_complete_comparison.csv")
        for _, row in df_all.iterrows():
            if row['asset'] in ['BTC', 'ETH']:
                # Estimate total return from avg_pnl * n_trades (rough approximation)
                est_total_return = row['avg_pnl'] * row['n_trades'] * 100
                
                results.append({
                    'Phase': 'Phase 2',
                    'Strategy': 'Pure Factor (Asymmetric)',
                    'Symbol': f"{row['asset']}USD",
                    'Timeframe': row['timeframe'],
                    'Period': '2017-2024 (7-8yr)',
                    'Exit Rule': 'Wide SL only',
                    'Total Return (%)': est_total_return,
                    'Sharpe': np.nan,
                    'Win Rate (%)': row['win_rate'] * 100,
                    'Num Trades': row['n_trades'],
                    'Avg PnL/Trade (%)': row['avg_pnl'] * 100,
                    'Max Drawdown (%)': np.nan,
                    'Notes': 'Extended to crypto'
                })
    except Exception as e:
        print(f"Warning: Could not load all_assets_complete_comparison.csv: {e}")
    
    # ========================================
    # Phase 3: Per-Trade Exit Rule Evaluation (All timeframes)
    # ========================================
    # From exit_rule_summary_table.csv
    try:
        df_exit = pd.read_csv(project_root / "results/exit_rule_summary_table.csv")
        for _, row in df_exit.iterrows():
            # Estimate total return from mean PnL * trades
            est_total_return = row['Mean PnL (%)'] * row['Trades']
            
            results.append({
                'Phase': 'Phase 3',
                'Strategy': 'Per-Trade Exit Evaluation',
                'Symbol': row['Symbol'],
                'Timeframe': row['Timeframe'],
                'Period': '2016-2024 (9yr)',
                'Exit Rule': row['Rule Name'],
                'Total Return (%)': est_total_return,
                'Sharpe': np.nan,
                'Win Rate (%)': row['Win Rate (%)'],
                'Num Trades': row['Trades'],
                'Avg PnL/Trade (%)': row['Mean PnL (%)'],
                'Max Drawdown (%)': np.nan,
                'Notes': f"{row['Rule Type']}"
            })
    except Exception as e:
        print(f"Warning: Could not load exit_rule_summary_table.csv: {e}")
    
    # ========================================
    # Phase 4: Portfolio-Level Backtest (4H only, latest)
    # ========================================
    # From portfolio_exit_rules_4h_compare_summary.csv
    try:
        df_portfolio = pd.read_csv(project_root / "results/portfolio_exit_rules_4h_compare_summary.csv")
        for _, row in df_portfolio.iterrows():
            results.append({
                'Phase': 'Phase 4 (LATEST)',
                'Strategy': 'Portfolio Backtest',
                'Symbol': row['symbol'],
                'Timeframe': row['timeframe'],
                'Period': '2016-2024 (9yr)',
                'Exit Rule': row['rule_name'],
                'Total Return (%)': row['total_return'] * 100,
                'Sharpe': row['sharpe'],
                'Win Rate (%)': row['win_rate'] * 100,
                'Num Trades': row['num_trades'],
                'Avg PnL/Trade (%)': row['avg_pnl_per_trade'] * 100,
                'Max Drawdown (%)': row['max_drawdown'] * 100,
                'Notes': f"Ann Return: {row['ann_return']*100:.2f}%"
            })
    except Exception as e:
        print(f"Warning: Could not load portfolio_exit_rules_4h_compare_summary.csv: {e}")
    
    return pd.DataFrame(results)


def main():
    """Generate complete strategy evolution table."""
    
    print("Loading all historical results...")
    df = load_all_results()
    
    if len(df) == 0:
        print("ERROR: No results loaded!")
        return
    
    print(f"Loaded {len(df)} strategy configurations")
    
    # Sort by Total Return descending
    df_sorted = df.sort_values('Total Return (%)', ascending=False)
    
    # Save full table
    out_path = project_root / "results/complete_strategy_evolution_table.csv"
    df_sorted.to_csv(out_path, index=False)
    print(f"\nSaved complete table to: {out_path}")
    
    # Display top 50
    print("\n" + "="*150)
    print("TOP 50 STRATEGIES BY TOTAL RETURN")
    print("="*150)
    
    display_cols = [
        'Phase', 'Strategy', 'Symbol', 'Timeframe', 'Exit Rule',
        'Total Return (%)', 'Sharpe', 'Win Rate (%)', 'Num Trades',
        'Avg PnL/Trade (%)', 'Max Drawdown (%)', 'Notes'
    ]
    
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 300)
    pd.set_option('display.max_rows', 50)
    
    print(df_sorted[display_cols].head(50).to_string(index=False))
    
    # Summary by phase
    print("\n" + "="*150)
    print("SUMMARY BY PHASE")
    print("="*150)
    
    phase_summary = df.groupby('Phase').agg({
        'Total Return (%)': ['mean', 'max', 'min'],
        'Sharpe': ['mean', 'max'],
        'Win Rate (%)': 'mean',
        'Num Trades': 'sum',
        'Symbol': 'count'
    }).round(2)
    
    print(phase_summary)
    
    # Summary by symbol
    print("\n" + "="*150)
    print("SUMMARY BY SYMBOL")
    print("="*150)
    
    symbol_summary = df.groupby('Symbol').agg({
        'Total Return (%)': ['mean', 'max', 'min'],
        'Sharpe': ['mean', 'max'],
        'Win Rate (%)': 'mean',
        'Num Trades': 'sum',
        'Phase': 'count'
    }).round(2)
    
    print(symbol_summary)
    
    # Summary by timeframe
    print("\n" + "="*150)
    print("SUMMARY BY TIMEFRAME")
    print("="*150)
    
    timeframe_summary = df.groupby('Timeframe').agg({
        'Total Return (%)': ['mean', 'max', 'min'],
        'Sharpe': ['mean', 'max'],
        'Win Rate (%)': 'mean',
        'Num Trades': 'sum',
        'Symbol': 'count'
    }).round(2)
    
    print(timeframe_summary)


if __name__ == "__main__":
    main()

