"""
Visualization tools for Extreme Reversal Strategy.

Provides plotting functions for:
- Equity curves
- Conditional return distributions
- Signal diagnostics
- Scatter plots and heatmaps
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, List
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def plot_equity_curve(
    equity: pd.Series,
    title: str = "Equity Curve",
    figsize: tuple = (14, 6),
    show_drawdown: bool = True
) -> plt.Figure:
    """
    绘制权益曲线。
    
    Plot equity curve with optional drawdown.
    
    Args:
        equity: Equity curve series
        title: Plot title
        figsize: Figure size
        show_drawdown: Whether to show drawdown subplot
    
    Returns:
        matplotlib Figure object
    """
    if show_drawdown:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, 
                                       gridspec_kw={'height_ratios': [2, 1]})
    else:
        fig, ax1 = plt.subplots(1, 1, figsize=figsize)
    
    # Plot equity curve
    ax1.plot(equity.index, equity.values, linewidth=1.5, label='Equity')
    ax1.axhline(y=equity.iloc[0], color='gray', linestyle='--', 
                alpha=0.5, label='Initial Capital')
    ax1.set_title(title, fontsize=14, fontweight='bold')
    ax1.set_ylabel('Equity', fontsize=12)
    ax1.legend(loc='best')
    ax1.grid(True, alpha=0.3)
    
    # Add return annotation
    total_return = (equity.iloc[-1] - equity.iloc[0]) / equity.iloc[0]
    ax1.text(0.02, 0.98, f'Total Return: {total_return:.2%}',
             transform=ax1.transAxes, fontsize=11,
             verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    if show_drawdown:
        # Calculate and plot drawdown
        cummax = equity.expanding().max()
        drawdown = (equity - cummax) / cummax
        
        ax2.fill_between(drawdown.index, drawdown.values, 0, 
                        alpha=0.3, color='red', label='Drawdown')
        ax2.plot(drawdown.index, drawdown.values, color='red', linewidth=1)
        ax2.set_ylabel('Drawdown', fontsize=12)
        ax2.set_xlabel('Time', fontsize=12)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        
        # Add max drawdown annotation
        max_dd = drawdown.min()
        ax2.text(0.02, 0.02, f'Max Drawdown: {max_dd:.2%}',
                transform=ax2.transAxes, fontsize=11,
                verticalalignment='bottom',
                bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))
    
    plt.tight_layout()
    return fig


def plot_conditional_returns(
    bars: pd.DataFrame,
    holding_horizon: int = 5,
    return_col: str = 'returns',
    signal_col: str = 'exec_signal',
    figsize: tuple = (14, 6)
) -> plt.Figure:
    """
    绘制条件收益分布。
    
    Plot conditional return distributions for different signal types.
    
    Args:
        bars: DataFrame with returns and signals
        holding_horizon: Forward-looking horizon for returns
        return_col: Name of return column
        signal_col: Name of signal column
        figsize: Figure size
    
    Returns:
        matplotlib Figure object
    """
    # Compute forward returns
    bars = bars.copy()
    bars['forward_return'] = bars[return_col].rolling(window=holding_horizon).sum().shift(-holding_horizon)
    
    # Separate by signal type
    long_signals = bars[bars[signal_col] == 1]['forward_return'].dropna()
    short_signals = bars[bars[signal_col] == -1]['forward_return'].dropna()
    no_signals = bars[bars[signal_col] == 0]['forward_return'].dropna()
    
    # Create figure
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    
    # Plot distributions
    if len(long_signals) > 0:
        axes[0].hist(long_signals, bins=50, alpha=0.7, color='green', edgecolor='black')
        axes[0].axvline(long_signals.mean(), color='darkgreen', linestyle='--', linewidth=2,
                       label=f'Mean: {long_signals.mean():.4%}')
        axes[0].axvline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        axes[0].set_title(f'Long Signals (n={len(long_signals)})', fontweight='bold')
        axes[0].set_xlabel(f'{holding_horizon}-bar Forward Return')
        axes[0].set_ylabel('Frequency')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
    
    if len(short_signals) > 0:
        # For short signals, we expect negative returns (price going down)
        axes[1].hist(short_signals, bins=50, alpha=0.7, color='red', edgecolor='black')
        axes[1].axvline(short_signals.mean(), color='darkred', linestyle='--', linewidth=2,
                       label=f'Mean: {short_signals.mean():.4%}')
        axes[1].axvline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        axes[1].set_title(f'Short Signals (n={len(short_signals)})', fontweight='bold')
        axes[1].set_xlabel(f'{holding_horizon}-bar Forward Return')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
    
    if len(no_signals) > 0:
        # Sample to avoid overcrowding
        sample_size = min(len(no_signals), 10000)
        no_signals_sample = no_signals.sample(n=sample_size, random_state=42)
        
        axes[2].hist(no_signals_sample, bins=50, alpha=0.7, color='gray', edgecolor='black')
        axes[2].axvline(no_signals_sample.mean(), color='black', linestyle='--', linewidth=2,
                       label=f'Mean: {no_signals_sample.mean():.4%}')
        axes[2].axvline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        axes[2].set_title(f'No Signal (n={len(no_signals)})', fontweight='bold')
        axes[2].set_xlabel(f'{holding_horizon}-bar Forward Return')
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_signal_diagnostics(
    bars: pd.DataFrame,
    manip_col: str = 'manip_score',
    figsize: tuple = (16, 10)
) -> plt.Figure:
    """
    绘制信号诊断图。

    Plot diagnostic charts for signal generation.
    """
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

    # 1. Scatter: R_past vs ManipScore
    ax1 = fig.add_subplot(gs[0, :])
    signals = bars['exec_signal'].fillna(0)
    colors = ['gray' if s == 0 else ('green' if s == 1 else 'red') for s in signals]

    ax1.scatter(bars['R_past'], bars[manip_col], c=colors, alpha=0.3, s=10)
    ax1.set_xlabel('R_past (Cumulative Return)', fontsize=12)
    ax1.set_ylabel('ManipScore', fontsize=12)
    ax1.set_title('Trend Strength vs ManipScore', fontsize=14, fontweight='bold')
    ax1.axhline(y=bars[manip_col].quantile(0.9), color='orange', linestyle='--', alpha=0.5)
    ax1.axvline(x=0, color='black', linestyle='-', alpha=0.3)
    ax1.grid(True, alpha=0.3)

    # 2. Signal distribution over time
    ax2 = fig.add_subplot(gs[1, 0])
    signal_counts = bars.groupby(bars.index.date)['exec_signal'].apply(lambda x: (x != 0).sum())
    ax2.plot(signal_counts.index, signal_counts.values, linewidth=1)
    ax2.set_xlabel('Date', fontsize=12)
    ax2.set_ylabel('Number of Signals', fontsize=12)
    ax2.set_title('Signal Frequency Over Time', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # 3. Trend strength distribution
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.hist(bars['abs_R_past'], bins=100, alpha=0.7, color='blue', edgecolor='black')
    ax3.axvline(bars['abs_R_past'].quantile(0.9), color='red', linestyle='--', linewidth=2)
    ax3.set_xlabel('|R_past|', fontsize=12)
    ax3.set_ylabel('Frequency', fontsize=12)
    ax3.set_title('Trend Strength Distribution', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)

    # 4. ManipScore distribution
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.hist(bars[manip_col], bins=100, alpha=0.7, color='orange', edgecolor='black')
    ax4.axvline(bars[manip_col].quantile(0.9), color='red', linestyle='--', linewidth=2)
    ax4.set_xlabel('ManipScore', fontsize=12)
    ax4.set_ylabel('Frequency', fontsize=12)
    ax4.set_title('ManipScore Distribution', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)

    # 5. Signal type breakdown
    ax5 = fig.add_subplot(gs[2, 1])
    signal_types = bars['exec_signal'].value_counts()
    values = [signal_types.get(0, 0), signal_types.get(1, 0), signal_types.get(-1, 0)]
    ax5.pie(values, labels=['No Signal', 'Long', 'Short'],
           colors=['gray', 'green', 'red'], autopct='%1.1f%%', startangle=90)
    ax5.set_title('Signal Distribution', fontsize=12, fontweight='bold')

    return fig


def plot_comprehensive_analysis(
    bars: pd.DataFrame,
    equity: pd.Series,
    trades: List,
    holding_horizon: int = 5,
    figsize: tuple = (18, 12)
) -> plt.Figure:
    """绘制综合分析图。"""
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(4, 2, hspace=0.4, wspace=0.3)

    # 1. Equity curve
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(equity.index, equity.values, linewidth=1.5, color='blue')
    ax1.set_title('Equity Curve', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Equity', fontsize=12)
    ax1.grid(True, alpha=0.3)

    # 2. Drawdown
    ax2 = fig.add_subplot(gs[1, :])
    cummax = equity.expanding().max()
    drawdown = (equity - cummax) / cummax
    ax2.fill_between(drawdown.index, drawdown.values, 0, alpha=0.3, color='red')
    ax2.plot(drawdown.index, drawdown.values, color='red', linewidth=1)
    ax2.set_title('Drawdown', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Drawdown', fontsize=12)
    ax2.grid(True, alpha=0.3)

    # 3. Trade PnL distribution
    ax3 = fig.add_subplot(gs[2, 0])
    trade_pnls = [t.pnl_pct for t in trades if t.pnl_pct is not None]
    if len(trade_pnls) > 0:
        ax3.hist(trade_pnls, bins=50, alpha=0.7, color='purple', edgecolor='black')
        ax3.axvline(np.mean(trade_pnls), color='darkred', linestyle='--', linewidth=2)
        ax3.axvline(0, color='black', linestyle='-', linewidth=1, alpha=0.5)
        ax3.set_xlabel('Trade PnL (%)', fontsize=12)
        ax3.set_ylabel('Frequency', fontsize=12)
        ax3.set_title('Trade PnL Distribution', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)

    # 4. Exit reason breakdown
    ax4 = fig.add_subplot(gs[2, 1])
    exit_reasons = [t.exit_reason for t in trades if t.exit_reason is not None]
    if len(exit_reasons) > 0:
        exit_counts = pd.Series(exit_reasons).value_counts()
        ax4.pie(exit_counts.values, labels=exit_counts.index, autopct='%1.1f%%', startangle=90)
        ax4.set_title('Exit Reasons', fontsize=12, fontweight='bold')

    plt.tight_layout()
    return fig

