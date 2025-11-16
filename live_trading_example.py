"""
实盘交易示例 - 仅使用K线数据

这个脚本展示如何使用K线数据进行实盘交易，不需要tick数据。

使用方法:
1. 首先运行训练模式: python live_trading_example.py --mode train
2. 然后运行实盘模式: python live_trading_example.py --mode live

依赖:
- ccxt (交易所API)
- pandas, numpy
- sklearn (用于ManipScore模型)
"""

import ccxt
import pandas as pd
import numpy as np
import pickle
import time
import argparse
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler


# ==================== ManipScore模型（简化版）====================

def fit_manipscore_model_simple(bars, bar_size='60min'):
    """
    拟合ManipScore模型（仅使用K线数据）
    
    特征: abs_ret_lag1, abs_ret_lag2 (滞后的绝对收益)
    目标: abs_ret (当前bar的绝对收益)
    """
    bars = bars.copy()
    
    # 计算收益率
    if 'returns' not in bars.columns:
        bars['returns'] = bars['close'].pct_change()
    
    # 计算绝对收益
    bars['abs_ret'] = bars['returns'].abs()
    
    # 创建滞后特征
    bars['abs_ret_lag1'] = bars['abs_ret'].shift(1)
    bars['abs_ret_lag2'] = bars['abs_ret'].shift(2)
    
    # 如果有volume，也使用它
    feature_cols = ['abs_ret_lag1', 'abs_ret_lag2']
    if 'volume' in bars.columns:
        feature_cols.append('volume')
    
    # 准备数据
    valid_mask = bars[feature_cols + ['abs_ret']].notna().all(axis=1)
    
    if valid_mask.sum() < 100:
        raise ValueError(f"数据不足: 只有{valid_mask.sum()}个有效样本，需要至少100个")
    
    X = bars.loc[valid_mask, feature_cols].values
    y = bars.loc[valid_mask, 'abs_ret'].values
    
    # 标准化特征
    scaler_X = StandardScaler()
    X_scaled = scaler_X.fit_transform(X)
    
    # 拟合线性回归
    regressor = LinearRegression()
    regressor.fit(X_scaled, y)
    
    # 计算残差
    y_pred = regressor.predict(X_scaled)
    residuals = y - y_pred
    
    # 统计量
    residual_mean = np.mean(residuals)
    residual_std = np.std(residuals)
    
    # 创建模型对象
    model = {
        'bar_size': bar_size,
        'feature_cols': feature_cols,
        'regressor': regressor,
        'scaler_X': scaler_X,
        'residual_mean': residual_mean,
        'residual_std': residual_std
    }
    
    print(f"ManipScore模型训练完成:")
    print(f"  - 特征: {feature_cols}")
    print(f"  - 样本数: {valid_mask.sum()}")
    print(f"  - 残差标准差: {residual_std:.6f}")
    
    return model


def apply_manipscore_simple(bars, model):
    """应用ManipScore模型"""
    bars = bars.copy()
    
    # 计算收益率
    if 'returns' not in bars.columns:
        bars['returns'] = bars['close'].pct_change()
    
    # 计算绝对收益
    bars['abs_ret'] = bars['returns'].abs()
    
    # 创建滞后特征
    bars['abs_ret_lag1'] = bars['abs_ret'].shift(1)
    bars['abs_ret_lag2'] = bars['abs_ret'].shift(2)
    
    # 准备特征
    X = bars[model['feature_cols']].values
    
    # 处理缺失值
    valid_mask = ~np.isnan(X).any(axis=1)
    
    # 初始化ManipScore
    bars['ManipScore'] = np.nan
    
    if valid_mask.sum() == 0:
        return bars
    
    # 标准化特征
    X_valid = X[valid_mask]
    X_scaled = model['scaler_X'].transform(X_valid)
    
    # 预测
    y_pred = model['regressor'].predict(X_scaled)
    
    # 实际值
    y_actual = bars.loc[valid_mask, 'abs_ret'].values
    
    # 计算残差
    residuals = y_actual - y_pred
    
    # 标准化 → ManipScore
    manip_scores = (residuals - model['residual_mean']) / (model['residual_std'] + 1e-8)
    
    # 赋值
    bars.loc[valid_mask, 'ManipScore'] = manip_scores
    
    return bars


# ==================== 趋势强度计算 ====================

def compute_trend_strength(bars, L_past=5, vol_window=20):
    """计算趋势强度"""
    bars = bars.copy()

    # 计算收益率
    if 'returns' not in bars.columns:
        bars['returns'] = bars['close'].pct_change()

    # 累计收益
    bars['R_past'] = bars['returns'].rolling(window=L_past, min_periods=1).sum()

    # 波动率
    bars['sigma'] = bars['returns'].rolling(window=vol_window, min_periods=1).std()
    bars['sigma'] = bars['sigma'].replace(0, np.nan)
    bars['sigma'] = bars['sigma'].fillna(method='ffill').fillna(bars['returns'].std())

    # 趋势强度
    bars['TS'] = bars['R_past'] / bars['sigma']

    return bars


# ==================== 训练模式 ====================

def train_mode(symbol='BTC/USDT', timeframe='1h', limit=5000):
    """训练模式：获取历史数据，训练模型，计算阈值"""
    print("=" * 80)
    print("训练模式")
    print("=" * 80)

    # 1. 初始化交易所
    print("\n步骤1: 连接交易所...")
    exchange = ccxt.binance()

    # 2. 获取历史数据
    print(f"\n步骤2: 获取历史K线数据 ({symbol}, {timeframe}, {limit}个bar)...")
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

    bars = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    bars['timestamp'] = pd.to_datetime(bars['timestamp'], unit='ms')
    bars.set_index('timestamp', inplace=True)

    print(f"  ✓ 获取了 {len(bars)} 个K线")
    print(f"  ✓ 时间范围: {bars.index[0]} 到 {bars.index[-1]}")

    # 3. 训练ManipScore模型
    print("\n步骤3: 训练ManipScore模型...")
    model = fit_manipscore_model_simple(bars, bar_size=timeframe)

    # 4. 计算阈值
    print("\n步骤4: 计算阈值...")
    bars = apply_manipscore_simple(bars, model)
    bars = compute_trend_strength(bars, L_past=5, vol_window=20)

    # 使用最近500个bar计算阈值
    recent_bars = bars.tail(500)
    threshold_TS = recent_bars['TS'].abs().quantile(0.9)
    threshold_MS = recent_bars['ManipScore'].quantile(0.9)

    print(f"  ✓ TS阈值 (90%分位数): {threshold_TS:.4f}")
    print(f"  ✓ ManipScore阈值 (90%分位数): {threshold_MS:.4f}")

    # 5. 保存模型和阈值
    print("\n步骤5: 保存模型和阈值...")

    model_path = Path('models')
    model_path.mkdir(exist_ok=True)

    with open(model_path / f'manipscore_model_{timeframe}.pkl', 'wb') as f:
        pickle.dump(model, f)

    thresholds = {
        'threshold_TS': threshold_TS,
        'threshold_MS': threshold_MS,
        'last_update': pd.Timestamp.now(),
        'symbol': symbol,
        'timeframe': timeframe
    }

    with open(model_path / f'thresholds_{timeframe}.pkl', 'wb') as f:
        pickle.dump(thresholds, f)

    print(f"  ✓ 模型已保存: {model_path / f'manipscore_model_{timeframe}.pkl'}")
    print(f"  ✓ 阈值已保存: {model_path / f'thresholds_{timeframe}.pkl'}")

    # 6. 验证
    print("\n步骤6: 验证信号生成...")
    extreme_up = bars['TS'] > threshold_TS
    extreme_down = bars['TS'] < -threshold_TS
    high_manip = bars['ManipScore'] > threshold_MS

    signals = ((extreme_up | extreme_down) & high_manip).astype(int)
    signal_count = signals.sum()
    signal_freq = signal_count / len(bars) * 100

    print(f"  ✓ 信号数量: {signal_count} / {len(bars)}")
    print(f"  ✓ 信号频率: {signal_freq:.2f}%")

    print("\n✅ 训练完成！")
    print("\n下一步: 运行实盘模式")
    print(f"  python {__file__} --mode live --symbol {symbol} --timeframe {timeframe}")


# ==================== 实盘模式 ====================

def live_mode(symbol='BTC/USDT', timeframe='1h', check_interval=3600):
    """实盘模式：实时监控并生成信号"""
    print("=" * 80)
    print("实盘模式")
    print("=" * 80)

    # 1. 加载模型和阈值
    print("\n步骤1: 加载模型和阈值...")

    model_path = Path('models')

    try:
        with open(model_path / f'manipscore_model_{timeframe}.pkl', 'rb') as f:
            model = pickle.load(f)

        with open(model_path / f'thresholds_{timeframe}.pkl', 'rb') as f:
            thresholds = pickle.load(f)

        print(f"  ✓ 模型已加载")
        print(f"  ✓ 阈值已加载 (更新时间: {thresholds['last_update']})")

    except FileNotFoundError:
        print("  ✗ 模型或阈值文件不存在")
        print("  请先运行训练模式: python live_trading_example.py --mode train")
        return

    threshold_TS = thresholds['threshold_TS']
    threshold_MS = thresholds['threshold_MS']

    # 2. 初始化交易所
    print("\n步骤2: 连接交易所...")
    exchange = ccxt.binance()

    print(f"\n开始监控 {symbol} ({timeframe})...")
    print(f"检查间隔: {check_interval}秒")
    print("-" * 80)

    # 3. 主循环
    while True:
        try:
            # 获取最新K线数据
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
            bars = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            bars['timestamp'] = pd.to_datetime(bars['timestamp'], unit='ms')
            bars.set_index('timestamp', inplace=True)

            # 应用ManipScore
            bars = apply_manipscore_simple(bars, model)

            # 计算趋势强度
            bars = compute_trend_strength(bars, L_past=5, vol_window=20)

            # 获取最新bar
            latest = bars.iloc[-1]

            # 生成信号
            extreme_up = latest['TS'] > threshold_TS
            extreme_down = latest['TS'] < -threshold_TS
            high_manip = latest['ManipScore'] > threshold_MS

            signal = 1 if (extreme_up or extreme_down) and high_manip else 0

            # 打印状态
            print(f"\n时间: {bars.index[-1]}")
            print(f"价格: {latest['close']:.2f}")
            print(f"TS: {latest['TS']:.4f} (阈值: ±{threshold_TS:.4f})")
            print(f"ManipScore: {latest['ManipScore']:.4f} (阈值: {threshold_MS:.4f})")
            print(f"极端上涨: {'✓' if extreme_up else '✗'}")
            print(f"极端下跌: {'✓' if extreme_down else '✗'}")
            print(f"高操纵: {'✓' if high_manip else '✗'}")

            if signal == 1:
                print("\n🚀 开仓信号！")
                print("=" * 80)
                # 这里添加实际的交易逻辑
                # order = exchange.create_market_buy_order(symbol, amount)
            else:
                print("信号: 无")

            # 等待下一次检查
            time.sleep(check_interval)

        except Exception as e:
            print(f"\n错误: {e}")
            print("60秒后重试...")
            time.sleep(60)


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description='实盘交易示例 - 仅使用K线数据')
    parser.add_argument('--mode', type=str, required=True, choices=['train', 'live'],
                       help='运行模式: train (训练) 或 live (实盘)')
    parser.add_argument('--symbol', type=str, default='BTC/USDT',
                       help='交易对 (默认: BTC/USDT)')
    parser.add_argument('--timeframe', type=str, default='1h',
                       help='时间周期 (默认: 1h)')
    parser.add_argument('--limit', type=int, default=5000,
                       help='训练模式下获取的K线数量 (默认: 5000)')
    parser.add_argument('--interval', type=int, default=3600,
                       help='实盘模式下的检查间隔（秒） (默认: 3600)')

    args = parser.parse_args()

    if args.mode == 'train':
        train_mode(symbol=args.symbol, timeframe=args.timeframe, limit=args.limit)
    else:
        live_mode(symbol=args.symbol, timeframe=args.timeframe, check_interval=args.interval)


if __name__ == '__main__':
    main()


