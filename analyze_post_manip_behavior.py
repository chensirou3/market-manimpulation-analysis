"""
分析高ManipScore后的市场行为
Analyze market behavior after high ManipScore
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

print("=" * 80)
print("高ManipScore后市场行为分析")
print("Market Behavior Analysis After High ManipScore")
print("=" * 80)
print()

# 加载数据
results_dir = Path('results')
all_files = sorted(results_dir.glob('bars_with_manipscore_*.csv'))

print(f"📁 加载 {len(all_files)} 个文件...")

# 合并所有数据
dfs = []
for i, f in enumerate(all_files, 1):
    if i % 10 == 0:
        print(f"  进度: {i}/{len(all_files)}")
    df = pd.read_csv(f, index_col=0, parse_dates=True)
    dfs.append(df)

bars = pd.concat(dfs, axis=0).sort_index()
print(f"✅ 总共 {len(bars):,} 根K线\n")

# 计算未来收益
print("📊 计算未来收益...")
for horizon in [1, 3, 5, 10, 20]:  # 未来1, 3, 5, 10, 20根K线
    bars[f'future_return_{horizon}'] = bars['close'].pct_change(horizon).shift(-horizon)

# 定义ManipScore等级
print("🎯 分类ManipScore等级...")
bars['manip_level'] = pd.cut(
    bars['manip_score'],
    bins=[0, 0.3, 0.5, 0.7, 1.0],
    labels=['低 (0-0.3)', '中低 (0.3-0.5)', '中高 (0.5-0.7)', '高 (0.7-1.0)']
)

# 分析每个等级的后续表现
print("\n" + "=" * 80)
print("不同ManipScore等级的后续市场表现")
print("=" * 80)
print()

results = []

for level in ['低 (0-0.3)', '中低 (0.3-0.5)', '中高 (0.5-0.7)', '高 (0.7-1.0)']:
    level_data = bars[bars['manip_level'] == level]
    
    if len(level_data) == 0:
        continue
    
    print(f"\n{level}:")
    print(f"  样本数: {len(level_data):,}")
    
    result = {
        'level': level,
        'count': len(level_data),
        'pct': len(level_data) / len(bars) * 100
    }
    
    for horizon in [1, 3, 5, 10, 20]:
        col = f'future_return_{horizon}'
        returns = level_data[col].dropna()
        
        if len(returns) > 0:
            mean_return = returns.mean()
            std_return = returns.std()
            positive_pct = (returns > 0).sum() / len(returns) * 100
            
            result[f'mean_{horizon}'] = mean_return
            result[f'std_{horizon}'] = std_return
            result[f'pos_{horizon}'] = positive_pct
            
            print(f"  未来{horizon}根K线:")
            print(f"    平均收益: {mean_return:>8.4%}")
            print(f"    标准差: {std_return:>8.4%}")
            print(f"    上涨概率: {positive_pct:>7.2f}%")
    
    results.append(result)

# 创建汇总表
print("\n\n" + "=" * 80)
print("汇总对比表")
print("=" * 80)
print()

summary_df = pd.DataFrame(results)

print("样本分布:")
print(summary_df[['level', 'count', 'pct']].to_string(index=False))

print("\n\n未来1根K线平均收益:")
print(summary_df[['level', 'mean_1', 'std_1', 'pos_1']].to_string(index=False))

print("\n未来5根K线平均收益:")
print(summary_df[['level', 'mean_5', 'std_5', 'pos_5']].to_string(index=False))

print("\n未来20根K线平均收益:")
print(summary_df[['level', 'mean_20', 'std_20', 'pos_20']].to_string(index=False))

# 保存结果
output_file = 'results/post_manip_analysis.csv'
summary_df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"\n✅ 结果已保存: {output_file}")

# 特别分析：高ManipScore (>0.7) 的详细情况
print("\n\n" + "=" * 80)
print("高ManipScore (>0.7) 详细分析")
print("=" * 80)
print()

high_manip = bars[bars['manip_score'] > 0.7].copy()
print(f"高ManipScore样本数: {len(high_manip):,} ({len(high_manip)/len(bars)*100:.2f}%)")

if len(high_manip) > 0:
    print("\n后续收益统计:")
    print("-" * 80)
    
    for horizon in [1, 3, 5, 10, 20]:
        col = f'future_return_{horizon}'
        returns = high_manip[col].dropna()
        
        if len(returns) > 0:
            print(f"\n未来{horizon}根K线 (约{horizon*5}分钟):")
            print(f"  平均收益: {returns.mean():>8.4%}")
            print(f"  中位数: {returns.median():>8.4%}")
            print(f"  标准差: {returns.std():>8.4%}")
            print(f"  最大涨幅: {returns.max():>8.4%}")
            print(f"  最大跌幅: {returns.min():>8.4%}")
            print(f"  上涨次数: {(returns > 0).sum():>6} ({(returns > 0).sum()/len(returns)*100:>5.2f}%)")
            print(f"  下跌次数: {(returns < 0).sum():>6} ({(returns < 0).sum()/len(returns)*100:>5.2f}%)")
            print(f"  不变次数: {(returns == 0).sum():>6} ({(returns == 0).sum()/len(returns)*100:>5.2f}%)")
    
    # 分析价格反转
    print("\n\n价格反转分析:")
    print("-" * 80)
    
    # 当前K线的涨跌
    high_manip['current_return'] = high_manip['close'].pct_change()
    high_manip['is_up'] = high_manip['current_return'] > 0
    
    for horizon in [1, 5, 10]:
        col = f'future_return_{horizon}'
        
        # 当前上涨后的反转
        up_bars = high_manip[high_manip['is_up'] == True]
        if len(up_bars) > 0:
            future_down = (up_bars[col] < 0).sum()
            print(f"\n当前上涨 → 未来{horizon}根K线:")
            print(f"  样本数: {len(up_bars)}")
            print(f"  反转下跌: {future_down} ({future_down/len(up_bars)*100:.2f}%)")
            print(f"  平均收益: {up_bars[col].mean():.4%}")
        
        # 当前下跌后的反转
        down_bars = high_manip[high_manip['is_up'] == False]
        if len(down_bars) > 0:
            future_up = (down_bars[col] > 0).sum()
            print(f"\n当前下跌 → 未来{horizon}根K线:")
            print(f"  样本数: {len(down_bars)}")
            print(f"  反转上涨: {future_up} ({future_up/len(down_bars)*100:.2f}%)")
            print(f"  平均收益: {down_bars[col].mean():.4%}")

# 波动率分析
print("\n\n" + "=" * 80)
print("波动率分析")
print("=" * 80)
print()

for level in ['低 (0-0.3)', '中低 (0.3-0.5)', '中高 (0.5-0.7)', '高 (0.7-1.0)']:
    level_data = bars[bars['manip_level'] == level]
    
    if len(level_data) > 0:
        # 计算未来波动率
        future_vol_5 = level_data['future_return_5'].abs().mean()
        future_vol_20 = level_data['future_return_20'].abs().mean()
        
        print(f"{level}:")
        print(f"  未来5根K线平均波动: {future_vol_5:.4%}")
        print(f"  未来20根K线平均波动: {future_vol_20:.4%}")

print("\n" + "=" * 80)
print("🎉 分析完成！")
print("=" * 80)

