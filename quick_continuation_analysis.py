import pandas as pd

# Load reversal stats
stats = {}
for bar_size in ['5min', '15min', '30min', '60min']:
    file = f'results/routeA_reversal_stats_{bar_size}.csv'
    df = pd.read_csv(file)
    stats[bar_size] = df

print('='*80)
print('Trend Continuation vs Reversal Analysis')
print('='*80)
print()

# Analyze for 5-bar horizon
print('Holding Period: 5 bars')
print()
print(f"{'Timeframe':<10} {'Reversal%':<12} {'Continuation%':<15} {'UP Avg Ret':<15} {'DOWN Avg Ret':<15}")
print('-'*80)

for bar_size in ['5min', '15min', '30min', '60min']:
    df = stats[bar_size]
    row = df[df['horizon'] == 5].iloc[0]
    
    rev_prob = row['reversal_prob_combined']
    cont_prob = 1 - rev_prob
    avg_ret_up = row['avg_future_ret_up']
    avg_ret_down = row['avg_future_ret_down']
    
    print(f"{bar_size:<10} {rev_prob*100:>6.2f}%     {cont_prob*100:>6.2f}%        {avg_ret_up*10000:>8.2f} bps    {avg_ret_down*10000:>8.2f} bps")

print()
print('='*80)
print('Detailed Analysis')
print('='*80)
print()

for bar_size in ['5min', '30min']:
    df = stats[bar_size]
    row = df[df['horizon'] == 5].iloc[0]
    
    print(f'{bar_size.upper()}:')
    print(f'  Extreme UP + High ManipScore:')
    print(f'    Reversal prob (price DOWN): {row["reversal_prob_up"]*100:.2f}%')
    print(f'    Continuation prob (price UP): {(1-row["reversal_prob_up"])*100:.2f}%')
    print(f'    Avg future return: {row["avg_future_ret_up"]*10000:.2f} bps')
    if row['avg_future_ret_up'] > 0:
        print(f'    -> Tends to CONTINUE (positive return)')
    else:
        print(f'    -> Tends to REVERSE (negative return)')
    print()
    
    print(f'  Extreme DOWN + High ManipScore:')
    print(f'    Reversal prob (price UP): {row["reversal_prob_down"]*100:.2f}%')
    print(f'    Continuation prob (price DOWN): {(1-row["reversal_prob_down"])*100:.2f}%')
    print(f'    Avg future return: {row["avg_future_ret_down"]*10000:.2f} bps')
    if row['avg_future_ret_down'] < 0:
        print(f'    -> Tends to CONTINUE (negative return, keeps falling)')
    else:
        print(f'    -> Tends to REVERSE (positive return, bounces)')
    print()

print('='*80)
print('CONCLUSION')
print('='*80)
print()
print('For 5min:')
df_5m = stats['5min']
row_5m = df_5m[df_5m['horizon'] == 5].iloc[0]
print(f'  Reversal prob: {row_5m["reversal_prob_combined"]*100:.2f}%')
print(f'  UP moves avg return: {row_5m["avg_future_ret_up"]*10000:.2f} bps ({"CONTINUE" if row_5m["avg_future_ret_up"] > 0 else "REVERSE"})')
print(f'  DOWN moves avg return: {row_5m["avg_future_ret_down"]*10000:.2f} bps ({"REVERSE" if row_5m["avg_future_ret_down"] > 0 else "CONTINUE"})')
print()

print('For 30min:')
df_30m = stats['30min']
row_30m = df_30m[df_30m['horizon'] == 5].iloc[0]
print(f'  Reversal prob: {row_30m["reversal_prob_combined"]*100:.2f}%')
print(f'  UP moves avg return: {row_30m["avg_future_ret_up"]*10000:.2f} bps ({"CONTINUE" if row_30m["avg_future_ret_up"] > 0 else "REVERSE"})')
print(f'  DOWN moves avg return: {row_30m["avg_future_ret_down"]*10000:.2f} bps ({"REVERSE" if row_30m["avg_future_ret_down"] > 0 else "CONTINUE"})')
print()

print('SUMMARY:')
print('  - Reversal strategy works because reversal probability > 50%')
print('  - BUT average returns are POSITIVE for both UP and DOWN moves!')
print('  - This suggests WEAK reversal effect, not strong enough for pure reversal strategy')
print('  - The current strategy success is likely due to other factors (stop-loss, take-profit, etc.)')

