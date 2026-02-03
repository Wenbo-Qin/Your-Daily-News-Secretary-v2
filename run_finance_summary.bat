@echo off
set LOGFILE=%~dp0finance_log.txt

echo ======================================== >> "%LOGFILE%"
echo %date% %time% - Start >> "%LOGFILE%"
echo ======================================== >> "%LOGFILE%"

cd /d "%~dp0"

echo Activating conda... >> "%LOGFILE%"
call conda activate finance_news
if %errorlevel% neq 0 (
    echo ERROR: conda activate failed >> "%LOGFILE%"
    echo %date% %time% - FAILED: conda activate failed >> "%LOGFILE%"
    goto :end
)

echo Running Python script... >> "%LOGFILE%"
python send_finance_summary.py >> "%LOGFILE%" 2>&1

echo %date% %time% - Done >> "%LOGFILE%"
echo. >> "%LOGFILE%"

:end
exit
