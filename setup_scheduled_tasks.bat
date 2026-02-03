@echo off
chcp 65001 >nul
echo ========================================
echo 设置财经新闻定时推送任务
echo ========================================
echo.

cd /d "%~dp0"

echo [1/5] 检测Conda环境...
where conda.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo   找到 conda.exe
    goto :found_conda
)

echo   [WARNING] 未在PATH中找到conda
echo   尝试常见conda路径...

REM 检查常见conda安装路径
if exist "C:\ProgramData\anaconda3\Scripts\conda.exe" (
    set "CONDA_EXE=C:\ProgramData\anaconda3\Scripts\conda.exe"
    set "CONDA_PATH=C:\ProgramData\anaconda3"
    goto :found_conda
)

if exist "C:\Users\%USERNAME%\anaconda3\Scripts\conda.exe" (
    set "CONDA_EXE=C:\Users\%USERNAME%\anaconda3\Scripts\conda.exe"
    set "CONDA_PATH=C:\Users\%USERNAME%\anaconda3"
    goto :found_conda
)

if exist "C:\ProgramData\miniconda3\Scripts\conda.exe" (
    set "CONDA_EXE=C:\ProgramData\miniconda3\Scripts\conda.exe"
    set "CONDA_PATH=C:\ProgramData\miniconda3"
    goto :found_conda
)

if exist "C:\Users\%USERNAME%\miniconda3\Scripts\conda.exe" (
    set "CONDA_EXE=C:\Users\%USERNAME%\miniconda3\Scripts\conda.exe"
    set "CONDA_PATH=C:\Users\%USERNAME%\miniconda3"
    goto :found_conda
)

echo   [ERROR] 未找到Conda，请确认conda已安装
echo.
echo 手动激活环境测试：
echo   conda activate chat-llm
echo   python "%~dp0send_finance_summary.py"
echo.
pause
exit /b 1

:found_conda
echo   Conda已找到
echo.

echo [2/5] 验证chat-llm环境...
call conda activate chat-llm
if %errorlevel% neq 0 (
    echo   [ERROR] chat-llm环境不存在或激活失败
    echo   可用环境：
    conda env list
    echo.
    echo 请先创建环境：conda create -n chat-llm python=3.x
    pause
    exit /b 1
)
echo   chat-llm环境已激活
where python.exe
echo.

echo [3/5] 删除旧任务...
schtasks /delete /tn "财经新闻早报" /f >nul 2>&1
schtasks /delete /tn "财经新闻晚报" /f >nul 2>&1
echo   旧任务已删除
echo.

REM 创建批处理文件来激活conda并运行脚本
set "RUNNER_BAT=%~dp0run_finance_summary.bat"

echo [4/5] 创建运行脚本...
echo @echo off > "%RUNNER_BAT%"
echo call conda activate chat-llm >> "%RUNNER_BAT%"
echo cd /d "%~dp0" >> "%RUNNER_BAT%"
echo python send_finance_summary.py >> "%RUNNER_BAT%"
echo   运行脚本已创建: %RUNNER_BAT%
echo.

echo [5/5] 创建定时任务...
schtasks /create /tn "财经新闻早报" /tr "\"%RUNNER_BAT%\"" /sc daily /st 08:00 /ru SYSTEM /f
if %errorlevel% neq (
    echo   [ERROR] 早报任务创建失败，错误代码: %errorlevel%
    goto :show_error
)
echo   早报任务创建成功

schtasks /create /tn "财经新闻晚报" /tr "\"%RUNNER_BAT%\"" /sc daily /st 18:00 /ru SYSTEM /f
if %errorlevel% neq (
    echo   [ERROR] 晚报任务创建失败，错误代码: %errorlevel%
    goto :show_error
)
echo   晚报任务创建成功
echo.

echo ========================================
echo 验证任务创建...
echo ========================================
schtasks /query /tn "财经新闻早报" /fo LIST
schtasks /query /tn "财经新闻晚报" /fo LIST

echo.
echo ========================================
echo 定时任务设置完成！
echo ========================================
echo.
echo 已创建任务：
echo - 财经新闻早报：每天 08:00
echo - 财经新闻晚报：每天 18:00
echo.
echo 运行脚本: %RUNNER_BAT%
echo.
echo 测试运行：
echo   %RUNNER_BAT%
echo.
echo 查看任务详情：
echo   schtasks /query /tn "财经新闻早报" /v
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
echo 1. 需要管理员权限 - 请右键以管理员身份运行此脚本
echo 2. 系统服务未运行
echo.
echo 手动测试（先激活conda环境）：
echo   conda activate chat-llm
echo   python "%~dp0send_finance_summary.py"
echo.
pause
exit /b 1
