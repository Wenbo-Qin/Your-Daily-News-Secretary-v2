@echo off
call conda activate chat-llm
cd /d "%~dp0"
python send_finance_summary.py
