@echo off
title Paster Builder
cd /d "%~dp0"
echo Building Paster...
echo.
pip install pyinstaller pyperclip keyboard -q
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul
del /q Paster.spec 2>nul
pyinstaller --onefile --windowed --name Paster Paster.py --clean --distpath dist --workpath build
if exist build rmdir /s /q build
if exist Paster.spec del /q Paster.spec
echo.
echo Done: dist\Paster.exe
pause
