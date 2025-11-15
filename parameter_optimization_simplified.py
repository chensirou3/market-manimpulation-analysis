"""
简化版参数优化系统
Simplified Parameter Optimization System

聚焦于最重要的参数，减少计算量
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
# 简化的参数空间 - 只优化最重要的参数
# ============================================================================

PARAM_GRID_SIMPLIFIED = {
    # 核心参数 - 根据测试结果，这些参数最重要
    'q_extreme_trend': np.arange(0.85, 0.98, 0.01),  # 0.85, 0.86, ..., 0.97 (13个)
    'q_manip': np.arange(0.85, 0.98, 0.01),          # 0.85, 0.86, ..., 0.97 (13个)
    'holding_horizon': [3, 5, 7, 10, 15, 20],        # 6个
    
    # 次要参数 - 使用较少的选项
    'L_past': [5, 7, 10],                            # 3个
    'min_abs_R_past': [0.003, 0.005, 0.007],         # 3个
    'sl_atr_mult': [0.5, 0.7, 1.0],                  # 3个
    'tp_atr_mult': [0.6, 0.8, 1.0, 1.5],             # 4个
    
    # 固定参数 - 不优化
    # vol_window: 20 (固定)
    # min_manip_score: 0.7 (固定)
    # use_normalized_trend: True (固定)
    # atr_window: 10 (固定)
    # cost_per_trade: 0.0001 (固定)
}

# 计算总组合数
total_combinations = np.prod([len(v) for v in PARAM_GRID_SIMPLIFIED.values()])
print(f"简化后总参数组合数: {total_combinations:,}")
print(f"相比原来的83,980,800，减少了 {83980800/total_combinations:.0f} 倍！")


# ============================================================================
# 网格搜索（全遍历）
# ============================================================================

def generate_all_combinations():
    """生成所有参数组合"""
    param_names = list(PARAM_GRID_SIMPLIFIED.keys())
    param_values_list = list(PARAM_GRID_SIMPLIFIED.values())
    
    samples = []
    for combo in product(*param_values_list):
        param_dict = dict(zip(param_names, combo))
        samples.append(param_dict)
    
    return samples


# ============================================================================
# 单次回测函数
# ============================================================================

def run_single_backtest_simplified(params_dict, bars, test_id):
    """运行单次回测（简化版）"""
    try:
        # 创建配置（使用固定的次要参数）
        config = ExtremeReversalConfig(
            L_past=int(params_dict['L_past']),
            vol_window=20,  # 固定
            q_extreme_trend=float(params_dict['q_extreme_trend']),
            use_normalized_trend=True,  # 固定
            min_abs_R_past=float(params_dict['min_abs_R_past']),
            q_manip=float(params_dict['q_manip']),
            min_manip_score=0.7,  # 固定
            holding_horizon=int(params_dict['holding_horizon']),
            atr_window=10,  # 固定
            sl_atr_mult=float(params_dict['sl_atr_mult']),
            tp_atr_mult=float(params_dict['tp_atr_mult']),
            cost_per_trade=0.0001  # 固定
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
        return None


# ============================================================================
# 主优化函数
# ============================================================================

def optimize_parameters_simplified(bars, n_workers=None, save_interval=100):
    """
    简化版参数优化
    
    Args:
        bars: 数据
        n_workers: 并行工作进程数
        save_interval: 保存间隔
    """
    print("=" * 80)
    print("简化版参数优化系统")
    print("=" * 80)
    print()
    
    # 生成所有参数组合
    print("【步骤 1】生成参数组合")
    print("-" * 80)
    
    param_samples = generate_all_combinations()
    
    print(f"✅ 生成 {len(param_samples):,} 个参数组合")
    print()
    
    # 准备数据
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
            executor.submit(run_single_backtest_simplified, params, bars_clean, i): i
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
            if completed % 50 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                speed = completed / elapsed
                remaining = (len(param_samples) - completed) / speed
                print(f"  进度: {completed}/{len(param_samples)} "
                      f"({completed/len(param_samples)*100:.1f}%) "
                      f"- 速度: {speed:.1f} tests/s "
                      f"- 剩余: {remaining/60:.1f} 分钟 "
                      f"- 有效: {len(results)}")
            
            # 定期保存中间结果
            if completed % save_interval == 0 and len(results) > 0:
                df_temp = pd.DataFrame(results)
                df_temp.to_csv('results/optimization_progress_simplified.csv', index=False)
    
    elapsed_total = (datetime.now() - start_time).total_seconds()
    print()
    print(f"✅ 回测完成！耗时: {elapsed_total/60:.1f} 分钟")
    print(f"   有效结果: {len(results)}/{len(param_samples)} ({len(results)/len(param_samples)*100:.1f}%)")
    print()
    
    return pd.DataFrame(results)

