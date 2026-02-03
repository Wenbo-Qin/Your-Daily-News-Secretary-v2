@echo off
chcp 65001 >nul
echo ========================================
echo 设置财经新闻定时推送任务
echo ========================================
echo.

cd /d "%~dp0"

echo [1/5] 检测Python环境...
where python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo   找到 python.exe
    set PYTHON_CMD=python
    goto :found_python
)

where py.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo   找到 py 启动器
    set PYTHON_CMD=py
    goto :found_python
)

echo   [ERROR] 未找到Python，请先安装Python并添加到PATH
echo   当前目录: %~dp0
echo   请手动运行: python send_finance_summary.py
echo.
pause
exit /b 1

:found_python
echo   使用命令: %PYTHON_CMD%
echo.

echo [2/5] 删除旧任务...
schtasks /delete /tn "财经新闻早报" /f >nul 2>&1
schtasks /delete /tn "财经新闻晚报" /f >nul 2>&1
echo   旧任务已删除
echo.

echo [3/5] 创建每日8:00早报任务...
schtasks /create /tn "财经新闻早报" /tr "%PYTHON_CMD% \"%~dp0send_finance_summary.py\"" /sc daily /st 08:00 /ru SYSTEM /f
if %errorlevel% neq (
    echo   [ERROR] 早报任务创建失败
    echo   错误代码: %errorlevel%
    goto :show_error
)
echo   早报任务创建成功
echo.

echo [4/5] 创建每日18:00晚报任务...
schtasks /create /tn "财经新闻晚报" /tr "%PYTHON_CMD% \"%~dp0send_finance_summary.py\"" /sc daily /st 18:00 /ru SYSTEM /f
if %errorlevel% neq (
    echo   [ERROR] 晚报任务创建失败
    echo   错误代码: %errorlevel%
    goto :show_error
)
echo   晚报任务创建成功
echo.

echo [5/5] 验证任务创建...
schtasks /query /tn "财经新闻早报" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] 财经新闻早报 - 已创建
) else (
    echo   [FAIL] 财经新闻早报 - 未创建
)

schtasks /query /tn "财经新闻晚报" >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] 财经新闻晚报 - 已创建
) else (
    echo   [FAIL] 财经新闻晚报 - 未创建
)

echo.
echo ========================================
echo 定时任务设置完成！
echo ========================================
echo.
echo 已创建任务：
echo - 财经新闻早报：每天 08:00
echo - 财经新闻晚报：每天 18:00
echo.
echo 查看详细信息：
echo   schtasks /query /tn "财经新闻早报" /v
echo   schtasks /query /tn "财经新闻晚报" /v
echo.
echo 测试运行：
echo   %PYTHON_CMD% "%~dp0send_finance_summary.py"
echo.
echo 删除任务：
echo   schtasks /delete /tn "财经新闻早报" /f
echo   schtasks /delete /tn "财经新闻晚报" /f
echo.
pause
exit /b 0

:show_error
echo.
echo ========================================
echo [ERROR] 任务创建失败
echo ========================================
echo.
echo 可能的原因：
echo 1. 需要管理员权限 - 请右键以管理员身份运行
echo 2. Python路径不正确
echo 3. 系统服务未运行
echo.
echo 手动创建命令：
echo   schtasks /create /tn "财经新闻早报" /tr "python \"%~dp0send_finance_summary.py\"" /sc daily /st 08:00
echo.
pause
exit /b 1
