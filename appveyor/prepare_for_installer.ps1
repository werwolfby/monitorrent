$targetDir="$PSScriptRoot\.."
Set-Location -Path $targetDir

Add-Type -AssemblyName System.IO.Compression.FileSystem
function Unzip
{
    param([string]$zipfile, [string]$outpath)

    [System.IO.Compression.ZipFile]::ExtractToDirectory($zipfile, $outpath)
}

<#  Download nssm#>
$nssmArchivePath = "$targetDir\nssm.zip"
$nssmFodlerPath="$targetDir\nssm"
$nssmExecutablePath=""
If (Test-Path $nssmArchivePath){
	Remove-Item $nssmArchivePath -recurse
}
If (Test-Path $nssmFodlerPath){
	Remove-Item $nssmFodlerPath -recurse
}

wget https://nssm.cc/release/nssm-2.24.zip -OutFile nssm.zip
Unzip $nssmArchivePath $nssmFodlerPath
Copy-Item $nssmFodlerPath\nssm-2.24\win32\nssm.exe .\nssm.exe

<#  Remove python help to save install size#>
Remove-Item -Recurse -Force "$targetDir\MonitorrentInstaller\env\Doc"

<#  Install web client#>
gulp dist