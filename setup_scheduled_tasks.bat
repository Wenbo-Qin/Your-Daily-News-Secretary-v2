@echo off
echo ========================================
echo Setup Finance News Scheduled Tasks
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Delete old tasks...
schtasks /delete /tn "FinanceMorning" /f >nul 2>&1
schtasks /delete /tn "FinanceEvening" /f >nul 2>&1
echo   Done
echo.

echo [2/3] Create daily 08:00 morning task...
schtasks /create /tn "FinanceMorning" /tr "\"%~dp0run_finance_summary.bat\"" /sc daily /st 08:00 /f
if %errorlevel% equ 0 (
    echo   Success
) else (
    echo   Failed - Need Admin Rights
)
echo.

echo [3/3] Create daily 18:00 evening task...
schtasks /create /tn "FinanceEvening" /tr "\"%~dp0run_finance_summary.bat\"" /sc daily /st 18:00 /f
if %errorlevel% equ 0 (
    echo   Success
) else (
    echo   Failed - Need Admin Rights
)
echo.

echo ========================================
echo Verify Tasks
echo ========================================
schtasks /query /tn "FinanceMorning" /fo LIST 2>nul
schtasks /query /tn "FinanceEvening" /fo LIST 2>nul
echo.

echo ========================================
echo Done!
echo ========================================
echo.
echo Runner: %~dp0run_finance_summary.bat
echo.
echo Manual test:
echo   run_finance_summary.bat
echo.
echo Delete tasks:
echo   schtasks /delete /tn "FinanceMorning" /f
echo   schtasks /delete /tn "FinanceEvening" /f
echo.
pause
