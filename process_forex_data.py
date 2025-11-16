"""
处理EURUSD和USDCHF的tick数据，生成OHLC bars并计算ManipScore

这个脚本将:
1. 读取parquet格式的tick数据
2. 聚合成不同时间周期的OHLC数据
3. 计算微观结构特征（N_ticks, spread_mean, RV等）
4. 计算ManipScore
5. 保存处理后的数据
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse
from typing import List
import glob
from tqdm import tqdm

# Import existing modules
import sys
sys.path.append(str(Path(__file__).parent))
from src.features.manipscore_model import fit_manipscore_model, apply_manipscore


def load_tick_data(symbol: str, data_dir: Path, start_year: int = 2022) -> pd.DataFrame:
    """
    加载指定symbol的tick数据（从start_year开始）

    Args:
        symbol: Symbol name (e.g., 'EURUSD')
        data_dir: Data directory path
        start_year: Only load data from this year onwards (default: 2022)
    """
    symbol_dir = data_dir / f"symbol={symbol}"
    if not symbol_dir.exists():
        raise FileNotFoundError(f"Directory not found: {symbol_dir}")

    # 获取所有parquet文件（在date=YYYY-MM-DD子目录中）
    all_parquet_files = sorted(glob.glob(str(symbol_dir / "date=*" / "*.parquet")))

    # 过滤：只保留start_year及之后的数据
    parquet_files = []
    for file in all_parquet_files:
        # 从文件名提取日期 (e.g., "EURUSD_2024-01-02.parquet")
        filename = Path(file).name
        try:
            year = int(filename.split('_')[1].split('-')[0])
            if year >= start_year:
                parquet_files.append(file)
        except:
            continue

    print(f"Found {len(parquet_files)} parquet files for {symbol} (from {start_year} onwards)")
    print(f"Total files in directory: {len(all_parquet_files)}")

    if len(parquet_files) == 0:
        raise FileNotFoundError(f"No parquet files found in {symbol_dir} for year >= {start_year}")

    # 读取所有文件并合并
    dfs = []
    for file in tqdm(parquet_files, desc=f"Loading {symbol} tick data"):
        df = pd.read_parquet(file)
        dfs.append(df)

    # 合并所有数据
    all_data = pd.concat(dfs, ignore_index=True)

    # 转换时间戳
    all_data['ts'] = pd.to_datetime(all_data['ts'])
    all_data = all_data.sort_values('ts').reset_index(drop=True)

    print(f"Loaded {len(all_data):,} ticks for {symbol}")
    print(f"Time range: {all_data['ts'].min()} to {all_data['ts'].max()}")

    return all_data


def create_ohlc_bars_with_features(tick_data: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """
    从tick数据创建OHLC bars并计算微观结构特征

    使用mid price (bid + ask) / 2
    同时计算: N_ticks, spread_mean, RV (realized volatility)
    """
    # 计算mid price和spread
    tick_data['mid'] = (tick_data['bid'] + tick_data['ask']) / 2
    tick_data['spread'] = tick_data['ask'] - tick_data['bid']
    tick_data['log_mid'] = np.log(tick_data['mid'])

    # 设置时间戳为索引
    tick_data = tick_data.set_index('ts')

    # 聚合成OHLC
    ohlc = tick_data['mid'].resample(timeframe).ohlc()

    # 计算微观结构特征
    # 1. N_ticks: 每个bar的tick数量
    N_ticks = tick_data['mid'].resample(timeframe).count()

    # 2. spread_mean: 平均价差
    spread_mean = tick_data['spread'].resample(timeframe).mean()

    # 3. RV: Realized Volatility (使用tick级别的log returns)
    tick_data['tick_ret'] = tick_data['log_mid'].diff()
    RV = (tick_data['tick_ret'] ** 2).resample(timeframe).sum()

    # 4. volume: 使用tick count作为proxy
    volume = N_ticks.copy()

    # 合并所有特征
    bars = pd.DataFrame({
        'open': ohlc['open'],
        'high': ohlc['high'],
        'low': ohlc['low'],
        'close': ohlc['close'],
        'volume': volume,
        'N_ticks': N_ticks,
        'spread_mean': spread_mean,
        'RV': RV
    })

    # 删除没有数据的行
    bars = bars.dropna(subset=['open', 'high', 'low', 'close'])

    # 重置索引，将时间戳作为列
    bars = bars.reset_index()
    bars.rename(columns={'ts': 'timestamp'}, inplace=True)

    print(f"Created {len(bars):,} bars for timeframe {timeframe}")
    print(f"Date range: {bars['timestamp'].min()} to {bars['timestamp'].max()}")
    print(f"Features: N_ticks (mean={bars['N_ticks'].mean():.1f}), spread_mean (mean={bars['spread_mean'].mean():.6f}), RV (mean={bars['RV'].mean():.8f})")

    return bars


def add_features_and_manipscore(bars: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """
    添加returns和ManipScore
    """
    # 计算returns
    bars['returns'] = bars['close'].pct_change()

    # 计算ManipScore
    print("Computing ManipScore...")

    # 拟合ManipScore模型
    try:
        model = fit_manipscore_model(
            bars=bars,
            bar_size=timeframe,
            feature_cols=None,  # Auto-detect features
            min_samples=500  # 降低最小样本要求
        )

        # 应用模型
        bars = apply_manipscore(bars, model)

        # 填充NaN为0
        bars['ManipScore'] = bars['ManipScore'].fillna(0)

        print(f"ManipScore computed: mean={bars['ManipScore'].mean():.3f}, std={bars['ManipScore'].std():.3f}")
        print(f"High ManipScore (>2): {(bars['ManipScore'] > 2).sum()} / {len(bars)}")

    except Exception as e:
        print(f"Warning: Failed to compute ManipScore: {e}")
        print("Setting ManipScore to 0")
        bars['ManipScore'] = 0

    return bars


def process_symbol(
    symbol: str,
    data_dir: Path,
    output_dir: Path,
    timeframes: List[str],
    start_year: int = 2022
):
    """
    处理单个symbol的完整流程
    """
    print(f"\n{'='*80}")
    print(f"Processing {symbol}")
    print(f"{'='*80}\n")

    # 1. 加载tick数据（从start_year开始）
    tick_data = load_tick_data(symbol, data_dir, start_year=start_year)

    # 2. 为每个时间周期创建OHLC bars
    for timeframe in timeframes:
        print(f"\n--- Processing timeframe: {timeframe} ---")

        # 创建OHLC bars with microstructure features
        bars = create_ohlc_bars_with_features(tick_data.copy(), timeframe)

        # 添加features和ManipScore
        bars = add_features_and_manipscore(bars, timeframe)

        # 保存数据
        output_file = output_dir / f"bars_{timeframe}_{symbol.lower()}_full_with_manipscore.csv"
        bars.to_csv(output_file, index=False)
        print(f"Saved to: {output_file}")
        print(f"Final shape: {bars.shape}")
        print(f"Columns: {bars.columns.tolist()}")


def main():
    parser = argparse.ArgumentParser(description="Process EURUSD and USDCHF tick data")
    parser.add_argument(
        '--symbols',
        nargs='+',
        default=['EURUSD', 'USDCHF'],
        help='Symbols to process'
    )
    parser.add_argument(
        '--timeframes',
        nargs='+',
        default=['5min', '15min', '30min', '60min', '4h', '1d'],
        help='Timeframes to generate'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='market-manimpulation-analysis/data',
        help='Directory containing tick data'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='market-manimpulation-analysis/results',
        help='Directory to save processed data'
    )
    parser.add_argument(
        '--start-year',
        type=int,
        default=2022,
        help='Only process data from this year onwards (default: 2022)'
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Processing data from {args.start_year} onwards")

    # 处理每个symbol
    for symbol in args.symbols:
        try:
            process_symbol(symbol, data_dir, output_dir, args.timeframes, start_year=args.start_year)
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n{'='*80}")
    print("Processing complete!")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()

