Updating installer:
1) Copy your python 3.7-3.8 environment to env folder in this directory.
2) Manually update new packages in PythonEnvironment.wsx.
3) install playwright browsers over powershell in this folder:
```powershell
$env:PLAYWRIGHT_BROWSERS_PATH="$(Get-Location)\browsers"
pip install playwright==1.20.0
playwright install firefox
```

All other files required by installation are collected dynamiacally during the build process.