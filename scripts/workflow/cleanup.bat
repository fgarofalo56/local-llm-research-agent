@echo off
REM Simple cleanup - delete unnecessary scripts
cd /d "%~dp0"

del /Q run-commit.bat 2>nul
del /Q check-status.bat 2>nul
del /Q git-status.bat 2>nul
del /Q git-add.bat 2>nul

echo Cleaned up unnecessary helper scripts
