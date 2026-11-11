@echo off
rem Starts Stungeon fullscreen from the repo folder (needs the .venv from the README setup).
cd /d "%~dp0"
".venv\Scripts\python.exe" main.py --fullscreen %*
