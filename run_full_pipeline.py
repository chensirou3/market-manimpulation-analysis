# -*- coding: utf-8 -*-
"""
完整流程演示 / Full Pipeline Demo
使用真实数据运行完整的交易操纵检测流程

流程:
1. 加载 tick 数据
2. 聚合为 K 线
3. 异常检测
4. 计算 ManipScore 因子
5. 策略回测
6. 性能对比
"""

import sys
import os

# 设置输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_prep.tick_loader import load_tick_data
from src.data_prep.bar_aggregator import ticks_to_bars
from src.anomaly.price_volume_anomaly import fit_price_volume_model, compute_price_volume_anomaly
from src.anomaly.volume_spike_anomaly import compute_volume_spike_score
from src.anomaly.structure_anomaly import detect_wash_trading, detect_extreme_candlesticks
from src.factors.manipulation_score import compute_manipulation_score
from src.backtest.interfaces import apply_manipulation_filter, calculate_performance_metrics, compare_strategies
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


def run_full_pipeline(
    start_date: str = '2024-01-01',
    end_date: str = '2024-12-31',
    timeframe: str = '5min',
    save_results: bool = True
):
    """
    运行完整的分析流程
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        timeframe: K 线周期
        save_results: 是否保存结果
    """
    
    print("=" * 80)
    print("🚀 开始运行完整流程")
    print("=" * 80)
    print(f"📅 日期范围: {start_date} 至 {end_date}")
    print(f"⏰ K 线周期: {timeframe}")
    print()
    
    # ========== 步骤 1: 加载数据 ==========
    print("=" * 80)
    print("步骤 1/6: 加载 Tick 数据")
    print("=" * 80)
    
    try:
        df_ticks = load_tick_data(start_date=start_date, end_date=end_date)
        
        print(f"✅ 成功加载 {len(df_ticks):,} 条 tick 数据")
        print(f"   时间范围: {df_ticks['timestamp'].min()} 至 {df_ticks['timestamp'].max()}")
        print(f"   数据大小: {df_ticks.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        print()
        
    except Exception as e:
        print(f"❌ 加载数据失败: {e}")
        return None
    
    # ========== 步骤 2: 聚合为 K 线 ==========
    print("=" * 80)
    print(f"步骤 2/6: 聚合为 {timeframe} K 线")
    print("=" * 80)
    
    try:
        df_bars = ticks_to_bars(df_ticks, timeframe=timeframe, compute_features=True)
        
        print(f"✅ 成功聚合为 {len(df_bars):,} 根 K 线")
        print(f"   时间范围: {df_bars.index.min()} 至 {df_bars.index.max()}")
        print(f"   列数: {len(df_bars.columns)}")
        print()
        
        # 显示前几行
        print("前 5 根 K 线:")
        print(df_bars[['open', 'high', 'low', 'close', 'volume']].head())
        print()
        
    except Exception as e:
        print(f"❌ 聚合失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # ========== 步骤 3: 异常检测 ==========
    print("=" * 80)
    print("步骤 3/6: 异常检测")
    print("=" * 80)
    
    try:
        # 3.1 价量异常
        print("3.1 检测价量异常...")
        pv_anomaly = compute_price_volume_anomaly(df_bars)
        pv_count = (pv_anomaly > 2).sum()
        print(f"   ✓ 检测到 {pv_count} 个价量异常点 (z-score > 2)")

        # 3.2 成交量突增
        print("3.2 检测成交量突增...")
        vol_spike = compute_volume_spike_score(df_bars)
        vs_count = (vol_spike > 2).sum()
        print(f"   ✓ 检测到 {vs_count} 个成交量突增点 (z-score > 2)")
        
        # 3.3 对敲检测
        print("3.3 检测对敲行为...")
        wash_index = detect_wash_trading(df_bars)
        wt_count = (wash_index > 1.5).sum()
        print(f"   ✓ 检测到 {wt_count} 个疑似对敲点 (wash_index > 1.5)")
        
        # 3.4 极端 K 线
        print("3.4 检测极端 K 线...")
        extreme_candles = detect_extreme_candlesticks(df_bars)
        ec_count = (extreme_candles > 0.7).sum()  # 使用阈值 0.7
        print(f"   ✓ 检测到 {ec_count} 个极端 K 线")
        print()
        
    except Exception as e:
        print(f"❌ 异常检测失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # ========== 步骤 4: 计算 ManipScore 因子 ==========
    print("=" * 80)
    print("步骤 4/6: 计算 ManipScore 因子")
    print("=" * 80)
    
    try:
        config = {
            'weights': {
                'price_volume': 0.25,
                'volume_spike': 0.25,
                'structure': 0.25,
                'wash_trade': 0.25
            },
            'normalize': True,
            'normalization_method': 'minmax',
            'smooth': False
        }

        df_bars_with_score = compute_manipulation_score(df_bars, config=config)
        manip_score = df_bars_with_score['manip_score']
        
        print(f"✅ 成功计算 ManipScore")
        print(f"   分数范围: {manip_score.min():.4f} - {manip_score.max():.4f}")
        print(f"   平均分数: {manip_score.mean():.4f}")
        print(f"   高分时段 (>0.7): {(manip_score > 0.7).sum()} 个 ({(manip_score > 0.7).sum() / len(manip_score) * 100:.2f}%)")
        print(f"   中分时段 (0.5-0.7): {((manip_score >= 0.5) & (manip_score <= 0.7)).sum()} 个")
        print(f"   低分时段 (<0.5): {(manip_score < 0.5).sum()} 个")
        print()
        
    except Exception as e:
        print(f"❌ 计算 ManipScore 失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # ========== 步骤 5: 生成模拟策略信号 ==========
    print("=" * 80)
    print("步骤 5/6: 生成模拟策略信号")
    print("=" * 80)
    
    try:
        # 简单的动量策略: 价格突破 20 周期均线
        df_bars['sma_20'] = df_bars['close'].rolling(20).mean()
        signals = (df_bars['close'] > df_bars['sma_20']).astype(int)
        
        signal_count = signals.sum()
        print(f"✅ 生成 {signal_count} 个买入信号 ({signal_count / len(signals) * 100:.2f}%)")
        print()
        
    except Exception as e:
        print(f"❌ 生成信号失败: {e}")
        return None
    
    # ========== 步骤 6: 应用操纵过滤并对比 ==========
    print("=" * 80)
    print("步骤 6/6: 应用操纵过滤并对比性能")
    print("=" * 80)
    
    try:
        # 应用过滤
        filtered_signals = apply_manipulation_filter(
            signals,
            manip_score,
            threshold=0.7,
            mode='zero'
        )
        
        filtered_count = filtered_signals.sum()
        filtered_pct = (signal_count - filtered_count) / signal_count * 100 if signal_count > 0 else 0
        
        print(f"✅ 过滤后剩余 {filtered_count} 个信号")
        print(f"   过滤掉 {signal_count - filtered_count} 个信号 ({filtered_pct:.2f}%)")
        print()
        
        # 对比性能
        print("性能对比:")
        print("-" * 80)

        # 计算收益率
        returns = df_bars['close'].pct_change()

        config = {
            'commission': 0.0002,
            'slippage': 0.0001
        }

        comparison = compare_strategies(
            returns,
            signals,
            filtered_signals,
            config=config
        )

        print(comparison)
        print()
        
    except Exception as e:
        print(f"❌ 性能对比失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # ========== 保存结果 ==========
    if save_results:
        print("=" * 80)
        print("保存结果")
        print("=" * 80)
        
        try:
            # 创建结果目录
            results_dir = Path('results')
            results_dir.mkdir(exist_ok=True)
            
            # 保存 K 线数据和因子
            output_file = results_dir / f'bars_with_manipscore_{start_date}_{end_date}.csv'
            df_output = df_bars.copy()
            df_output['manip_score'] = manip_score
            df_output['pv_anomaly'] = pv_anomaly
            df_output['vol_spike'] = vol_spike
            df_output['wash_index'] = wash_index
            df_output['extreme_candle'] = extreme_candles
            df_output['signal'] = signals
            df_output['filtered_signal'] = filtered_signals
            
            df_output.to_csv(output_file)
            print(f"✅ 结果已保存至: {output_file}")
            print(f"   文件大小: {output_file.stat().st_size / 1024:.2f} KB")
            print()
            
        except Exception as e:
            print(f"⚠️  保存结果失败: {e}")
    
    # ========== 总结 ==========
    print("=" * 80)
    print("✅ 流程完成！")
    print("=" * 80)
    print()
    print("📊 数据统计:")
    print(f"   - Tick 数据: {len(df_ticks):,} 条")
    print(f"   - K 线数据: {len(df_bars):,} 根")
    print(f"   - 异常点: PV={pv_count}, VS={vs_count}, WT={wt_count}, EC={ec_count}")
    print(f"   - 高操纵分数: {(manip_score > 0.7).sum()} 个")
    print(f"   - 原始信号: {signal_count} 个")
    print(f"   - 过滤后信号: {filtered_count} 个")
    print()
    
    return {
        'df_ticks': df_ticks,
        'df_bars': df_bars,
        'manip_score': manip_score,
        'signals': signals,
        'filtered_signals': filtered_signals,
        'comparison': comparison
    }


if __name__ == "__main__":
    # 运行完整流程 - 使用 2024 年 1 月的数据作为示例
    # 如果要运行整年，将 end_date 改为 '2024-12-31'

    print("\n")
    print("=" * 80)
    print("运行完整的交易操纵检测流程")
    print("使用 2024 年 1 月数据作为示例")
    print("=" * 80)
    print()
    
    results = run_full_pipeline(
        start_date='2024-01-01',
        end_date='2024-01-31',  # 先用 1 个月测试
        timeframe='5min',
        save_results=True
    )
    
    if results:
        print("=" * 80)
        print("流程运行成功！")
        print("=" * 80)
        print()
        print("提示:")
        print("   - 查看 results/ 目录获取详细结果")
        print("   - 修改日期范围可以分析更长时间段")
        print("   - 调整 timeframe 可以使用不同的 K 线周期")
        print()

