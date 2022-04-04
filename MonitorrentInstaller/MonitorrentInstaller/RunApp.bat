@echo off
SET PLAYWRIGHT_BROWSERS_PATH="%~dp0/browsers"
"%~dp0/env/python" "%~dp0/server.py"