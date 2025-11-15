"""
参数优化系统 - 多线程加速版
Parameter Optimization System - Multi-threaded

使用网格搜索 + 多线程并行计算来优化策略参数
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
import warnings
warnings.filterwarnings('ignore')

from src.strategies import (
    ExtremeReversalConfig,
    generate_extreme_reversal_signals,
    run_extreme_reversal_backtest
)


# ============================================================================
# 参数空间定义
# ============================================================================

PARAM_GRID = {
    # 趋势参数
    'L_past': [3, 5, 7, 10, 15, 20],  # 回看窗口
    'vol_window': [10, 15, 20, 30, 50],  # 波动率窗口
    'q_extreme_trend': np.arange(0.80, 0.98, 0.02),  # 0.80, 0.82, ..., 0.96
    'min_abs_R_past': [0.001, 0.003, 0.005, 0.007, 0.010, 0.015],  # 最小变动
    
    # ManipScore参数
    'q_manip': np.arange(0.80, 0.98, 0.02),  # 0.80, 0.82, ..., 0.96
    'min_manip_score': [0.5, 0.6, 0.7, 0.8, 0.9],  # 最小ManipScore
    
    # 执行参数
    'holding_horizon': [3, 5, 7, 10, 15, 20],  # 持仓时间
    'sl_atr_mult': np.arange(0.3, 1.5, 0.1),  # 0.3, 0.4, ..., 1.4
    'tp_atr_mult': np.arange(0.4, 2.0, 0.1),  # 0.4, 0.5, ..., 1.9
}

# 计算总组合数
total_combinations = np.prod([len(v) for v in PARAM_GRID.values()])
print(f"总参数组合数: {total_combinations:,}")
print("这个数量太大，我们需要使用智能采样策略！")


# ============================================================================
# 智能采样策略
# ============================================================================

def generate_smart_samples(n_samples=1000, random_seed=42):
    """
    使用拉丁超立方采样 (Latin Hypercube Sampling) 生成参数组合
    这样可以用更少的样本覆盖整个参数空间
    """
    np.random.seed(random_seed)
    
    samples = []
    
    # 为每个参数生成均匀分布的索引
    n_params = len(PARAM_GRID)
    lhs_indices = np.zeros((n_samples, n_params), dtype=int)
    
    for i, (param_name, param_values) in enumerate(PARAM_GRID.items()):
        # 生成0到n_samples-1的随机排列
        perm = np.random.permutation(n_samples)
        # 映射到参数值的索引
        lhs_indices[:, i] = (perm * len(param_values) // n_samples).astype(int)
    
    # 生成参数组合
    param_names = list(PARAM_GRID.keys())
    param_values_list = list(PARAM_GRID.values())
    
    for idx_row in lhs_indices:
        param_dict = {}
        for i, param_name in enumerate(param_names):
            param_dict[param_name] = param_values_list[i][idx_row[i]]
        samples.append(param_dict)
    
    return samples


def generate_grid_samples(step=2):
    """
    生成网格采样（每隔step个取一个）
    """
    samples = []
    
    param_names = list(PARAM_GRID.keys())
    param_values_list = [list(v)[::step] for v in PARAM_GRID.values()]
    
    for combo in product(*param_values_list):
        param_dict = dict(zip(param_names, combo))
        samples.append(param_dict)
    
    return samples


# ============================================================================
# 单次回测函数（用于并行）
# ============================================================================

def run_single_backtest(params_dict, bars, test_id):
    """
    运行单次回测
    
    Args:
        params_dict: 参数字典
        bars: 数据
        test_id: 测试ID
    
    Returns:
        结果字典
    """
    try:
        # 创建配置
        config = ExtremeReversalConfig(
            L_past=int(params_dict['L_past']),
            vol_window=int(params_dict['vol_window']),
            q_extreme_trend=float(params_dict['q_extreme_trend']),
            use_normalized_trend=True,
            min_abs_R_past=float(params_dict['min_abs_R_past']),
            q_manip=float(params_dict['q_manip']),
            min_manip_score=float(params_dict['min_manip_score']),
            holding_horizon=int(params_dict['holding_horizon']),
            atr_window=10,
            sl_atr_mult=float(params_dict['sl_atr_mult']),
            tp_atr_mult=float(params_dict['tp_atr_mult']),
            cost_per_trade=0.0001
        )
        
        # 生成信号
        bars_with_signals = generate_extreme_reversal_signals(bars.copy(), config)
        
        n_signals = (bars_with_signals['exec_signal'] != 0).sum()
        
        # 如果信号太少，跳过
        if n_signals < 10:
            return None
        
        # 运行回测
        result = run_extreme_reversal_backtest(
            bars_with_signals,
            bars_with_signals['exec_signal'],
            config,
            initial_capital=10000.0
        )
        
        # 提取结果
        result_dict = {
            'test_id': test_id,
            **params_dict,
            'n_signals': n_signals,
            'n_trades': result.stats.get('n_trades', 0),
            'total_return': result.stats.get('total_return', 0),
            'annualized_return': result.stats.get('annualized_return', 0),
            'sharpe_ratio': result.stats.get('sharpe_ratio', 0),
            'max_drawdown': result.stats.get('max_drawdown', 0),
            'win_rate': result.stats.get('win_rate', 0),
            'profit_factor': result.stats.get('profit_factor', 0),
            'avg_bars_held': result.stats.get('avg_bars_held', 0),
        }
        
        return result_dict
        
    except Exception as e:
        print(f"测试 {test_id} 失败: {str(e)}")
        return None


# ============================================================================
# 主优化函数
# ============================================================================

def optimize_parameters(
    bars,
    n_samples=500,
    sampling_method='lhs',  # 'lhs' or 'grid'
    n_workers=None,
    save_interval=50
):
    """
    参数优化主函数
    
    Args:
        bars: 数据
        n_samples: 采样数量
        sampling_method: 采样方法 ('lhs' 或 'grid')
        n_workers: 并行工作进程数（None=自动）
        save_interval: 每隔多少次保存一次中间结果
    """
    print("=" * 80)
    print("参数优化系统")
    print("=" * 80)
    print()
    
    # 生成参数样本
    print(f"【步骤 1】生成参数样本 (方法: {sampling_method})")
    print("-" * 80)
    
    if sampling_method == 'lhs':
        param_samples = generate_smart_samples(n_samples=n_samples)
    else:
        param_samples = generate_grid_samples(step=2)
    
    print(f"✅ 生成 {len(param_samples)} 个参数组合")
    print()
    
    # 准备数据（确保数据可以被pickle）
    print("【步骤 2】准备数据")
    print("-" * 80)
    bars_clean = bars.copy()
    print(f"✅ 数据准备完成: {len(bars_clean):,} 根K线")
    print()
    
    # 并行回测
    print("【步骤 3】并行回测")
    print("-" * 80)
    
    if n_workers is None:
        import multiprocessing
        n_workers = max(1, multiprocessing.cpu_count() - 1)
    
    print(f"使用 {n_workers} 个并行进程")
    print(f"预计时间: {len(param_samples) * 2 / n_workers / 60:.1f} 分钟")
    print()
    
    results = []
    start_time = datetime.now()
    
    # 使用ProcessPoolExecutor进行并行计算
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        # 提交所有任务
        futures = {
            executor.submit(run_single_backtest, params, bars_clean, i): i
            for i, params in enumerate(param_samples)
        }
        
        # 收集结果
        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            
            if result is not None:
                results.append(result)
            
            # 进度显示
            if completed % 10 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                speed = completed / elapsed
                remaining = (len(param_samples) - completed) / speed
                print(f"  进度: {completed}/{len(param_samples)} "
                      f"({completed/len(param_samples)*100:.1f}%) "
                      f"- 速度: {speed:.1f} tests/s "
                      f"- 剩余: {remaining/60:.1f} 分钟")
            
            # 定期保存中间结果
            if completed % save_interval == 0 and len(results) > 0:
                df_temp = pd.DataFrame(results)
                df_temp.to_csv('results/optimization_progress.csv', index=False)
                print(f"  💾 中间结果已保存 ({len(results)} 个有效结果)")
    
    elapsed_total = (datetime.now() - start_time).total_seconds()
    print()
    print(f"✅ 回测完成！耗时: {elapsed_total/60:.1f} 分钟")
    print(f"   有效结果: {len(results)}/{len(param_samples)} ({len(results)/len(param_samples)*100:.1f}%)")
    print()

    return pd.DataFrame(results)


# ============================================================================
# 结果分析函数
# ============================================================================

def analyze_optimization_results(df_results):
    """分析优化结果"""

    print("=" * 80)
    print("优化结果分析")
    print("=" * 80)
    print()

    # 基本统计
    print("📊 基本统计:")
    print(f"  总测试数: {len(df_results)}")
    print(f"  平均收益: {df_results['total_return'].mean()*100:.2f}%")
    print(f"  收益标准差: {df_results['total_return'].std()*100:.2f}%")
    print(f"  最佳收益: {df_results['total_return'].max()*100:.2f}%")
    print(f"  最差收益: {df_results['total_return'].min()*100:.2f}%")
    print(f"  盈利比例: {(df_results['total_return'] > 0).sum() / len(df_results) * 100:.1f}%")
    print()

    # Top 10 参数组合
    print("🏆 Top 10 参数组合 (按总收益):")
    print("-" * 80)
    top10 = df_results.nlargest(10, 'total_return')

    for i, row in top10.iterrows():
        print(f"\n#{row['test_id']} - 收益: {row['total_return']*100:.2f}% | "
              f"Sharpe: {row['sharpe_ratio']:.2f} | 胜率: {row['win_rate']*100:.1f}%")
        print(f"  L_past={row['L_past']}, vol_win={row['vol_window']}, "
              f"q_trend={row['q_extreme_trend']:.2f}, q_manip={row['q_manip']:.2f}")
        print(f"  min_R={row['min_abs_R_past']:.3f}, min_manip={row['min_manip_score']:.1f}, "
              f"horizon={row['holding_horizon']}")
        print(f"  SL={row['sl_atr_mult']:.1f}, TP={row['tp_atr_mult']:.1f}, "
              f"信号数={row['n_signals']}")

    print()

    # 按Sharpe排序
    print("🏆 Top 10 参数组合 (按Sharpe比率):")
    print("-" * 80)
    top10_sharpe = df_results.nlargest(10, 'sharpe_ratio')

    for i, row in top10_sharpe.iterrows():
        print(f"\n#{row['test_id']} - Sharpe: {row['sharpe_ratio']:.2f} | "
              f"收益: {row['total_return']*100:.2f}% | 胜率: {row['win_rate']*100:.1f}%")
        print(f"  L_past={row['L_past']}, q_trend={row['q_extreme_trend']:.2f}, "
              f"q_manip={row['q_manip']:.2f}, horizon={row['holding_horizon']}")

    print()

    # 参数重要性分析
    print("📈 参数重要性分析 (与收益的相关性):")
    print("-" * 80)

    param_cols = ['L_past', 'vol_window', 'q_extreme_trend', 'min_abs_R_past',
                  'q_manip', 'min_manip_score', 'holding_horizon',
                  'sl_atr_mult', 'tp_atr_mult']

    correlations = {}
    for col in param_cols:
        corr = df_results[col].corr(df_results['total_return'])
        correlations[col] = corr

    # 排序
    sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)

    for param, corr in sorted_corr:
        direction = "↑" if corr > 0 else "↓"
        print(f"  {param:20s}: {corr:>7.3f} {direction}")

    print()

    return top10, top10_sharpe


def visualize_optimization_results(df_results, save_path='results/optimization_analysis.png'):
    """可视化优化结果"""

    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)

    # 1. 收益分布
    ax1 = fig.add_subplot(gs[0, :2])
    ax1.hist(df_results['total_return'] * 100, bins=50, alpha=0.7,
             color='blue', edgecolor='black')
    ax1.axvline(0, color='red', linestyle='--', linewidth=2)
    ax1.set_xlabel('总收益 (%)', fontsize=12)
    ax1.set_ylabel('频数', fontsize=12)
    ax1.set_title('收益分布', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # 2. Sharpe分布
    ax2 = fig.add_subplot(gs[0, 2:])
    ax2.hist(df_results['sharpe_ratio'], bins=50, alpha=0.7,
             color='green', edgecolor='black')
    ax2.axvline(0, color='red', linestyle='--', linewidth=2)
    ax2.set_xlabel('Sharpe比率', fontsize=12)
    ax2.set_ylabel('频数', fontsize=12)
    ax2.set_title('Sharpe比率分布', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # 3-6. 关键参数 vs 收益
    param_plots = [
        ('q_extreme_trend', '极端趋势阈值'),
        ('q_manip', 'ManipScore阈值'),
        ('holding_horizon', '持仓时间'),
        ('sl_atr_mult', '止损倍数')
    ]

    for idx, (param, label) in enumerate(param_plots):
        ax = fig.add_subplot(gs[1, idx])
        scatter = ax.scatter(df_results[param], df_results['total_return'] * 100,
                           c=df_results['sharpe_ratio'], cmap='RdYlGn',
                           alpha=0.6, s=20)
        ax.set_xlabel(label, fontsize=11)
        ax.set_ylabel('收益 (%)', fontsize=11)
        ax.set_title(f'{label} vs 收益', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax, label='Sharpe')

    # 7. 胜率 vs 收益
    ax7 = fig.add_subplot(gs[2, 0])
    ax7.scatter(df_results['win_rate'] * 100, df_results['total_return'] * 100,
               alpha=0.5, s=20)
    ax7.set_xlabel('胜率 (%)', fontsize=12)
    ax7.set_ylabel('收益 (%)', fontsize=12)
    ax7.set_title('胜率 vs 收益', fontsize=12, fontweight='bold')
    ax7.grid(True, alpha=0.3)

    # 8. 信号数 vs 收益
    ax8 = fig.add_subplot(gs[2, 1])
    ax8.scatter(df_results['n_signals'], df_results['total_return'] * 100,
               alpha=0.5, s=20, color='orange')
    ax8.set_xlabel('信号数', fontsize=12)
    ax8.set_ylabel('收益 (%)', fontsize=12)
    ax8.set_title('信号数 vs 收益', fontsize=12, fontweight='bold')
    ax8.grid(True, alpha=0.3)

    # 9. 盈亏比 vs 收益
    ax9 = fig.add_subplot(gs[2, 2])
    ax9.scatter(df_results['profit_factor'], df_results['total_return'] * 100,
               alpha=0.5, s=20, color='purple')
    ax9.set_xlabel('盈亏比', fontsize=12)
    ax9.set_ylabel('收益 (%)', fontsize=12)
    ax9.set_title('盈亏比 vs 收益', fontsize=12, fontweight='bold')
    ax9.grid(True, alpha=0.3)

    # 10. 最大回撤 vs 收益
    ax10 = fig.add_subplot(gs[2, 3])
    ax10.scatter(df_results['max_drawdown'] * 100, df_results['total_return'] * 100,
                alpha=0.5, s=20, color='red')
    ax10.set_xlabel('最大回撤 (%)', fontsize=12)
    ax10.set_ylabel('收益 (%)', fontsize=12)
    ax10.set_title('最大回撤 vs 收益', fontsize=12, fontweight='bold')
    ax10.grid(True, alpha=0.3)

    plt.suptitle('参数优化结果分析', fontsize=16, fontweight='bold')
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"✅ 可视化结果已保存: {save_path}")

    return fig

