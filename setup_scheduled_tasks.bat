@echo off
chcp 65001 >nul
echo ========================================
echo 设置财经新闻定时推送任务
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 删除旧任务...
schtasks /delete /tn "财经新闻早报" /f >nul 2>&1
schtasks /delete /tn "财经新闻晚报" /f >nul 2>&1
echo   完成
echo.

echo [2/3] 创建每日8:00早报任务...
schtasks /create /tn "财经新闻早报" /tr "\"%~dp0run_finance_summary.bat\"" /sc daily /st 08:00 /f
if %errorlevel% equ 0 (
    echo   成功
) else (
    echo   失败（需要管理员权限）
)
echo.

echo [3/3] 创建每日18:00晚报任务...
schtasks /create /tn "财经新闻晚报" /tr "\"%~dp0run_finance_summary.bat\"" /sc daily /st 18:00 /f
if %errorlevel% equ 0 (
    echo   成功
) else (
    echo   失败（需要管理员权限）
)
echo.

echo ========================================
echo 验证任务
echo ========================================
schtasks /query /tn "财经新闻早报" /fo LIST 2>nul
schtasks /query /tn "财经新闻晚报" /fo LIST 2>nul
echo.

echo ========================================
echo 完成！
echo ========================================
echo.
echo 运行脚本: %~dp0run_finance_summary.bat
echo.
echo 手动测试:
echo   run_finance_summary.bat
echo.
echo 删除任务:
echo   schtasks /delete /tn "财经新闻早报" /f
echo   schtasks /delete /tn "财经新闻晚报" /f
echo.
pause
