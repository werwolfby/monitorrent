@echo off
SET PLAYWRIGHT_BROWSERS_PATH="%~dp0/browsers"
"%~dp0/nssm.exe" restart monitorrent