@echo off
chcp 65001
echo ================================================================================
echo 开始运行全数据分析 (2015-2025)
echo Start running all data analysis (2015-2025)
echo ================================================================================
echo.

python run_all_data_by_quarter.py > output_all_data.txt 2>&1

echo.
echo ================================================================================
echo 处理完成！查看 output_all_data.txt 了解详情
echo Processing complete! Check output_all_data.txt for details
echo ================================================================================
echo.

pause

