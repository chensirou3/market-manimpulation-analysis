@echo off
chcp 65001
echo ================================================================================
echo 运行全部年份数据分析 (2015-2025)
echo Run All Years Analysis (2015-2025)
echo ================================================================================
echo.

REM 处理 2015-2023 年
for %%y in (2015 2016 2017 2018 2019 2020 2021 2022 2023) do (
    echo.
    echo ================================================================================
    echo 处理 %%y 年
    echo Processing %%y
    echo ================================================================================
    python run_by_quarter.py %%y
    if errorlevel 1 (
        echo 错误: %%y 年处理失败
    ) else (
        echo 成功: %%y 年处理完成
    )
)

REM 处理 2025 年 (只有3个季度)
echo.
echo ================================================================================
echo 处理 2025 年 (Q1-Q3)
echo Processing 2025 (Q1-Q3)
echo ================================================================================
python -c "from run_by_quarter import run_by_quarter; run_by_quarter(2025)"

echo.
echo ================================================================================
echo 全部完成！
echo All Done!
echo ================================================================================
echo.

REM 合并所有汇总文件
echo 正在合并汇总文件...
python -c "import pandas as pd; import glob; dfs = [pd.read_csv(f) for f in glob.glob('results/summary_*_by_quarter.csv')]; pd.concat(dfs).to_csv('results/summary_all_years.csv', index=False); print('汇总文件已保存: results/summary_all_years.csv')"

pause

