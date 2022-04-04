@echo off
SET PLAYWRIGHT_BROWSERS_PATH="%~dp0/browsers"
"%~dp0/nssm.exe" install monitorrent "%~dp0/RunApp.bat"