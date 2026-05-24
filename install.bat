@echo off
setlocal
set "TARGET=%USERPROFILE%\.local\bin"
if not exist "%TARGET%" mkdir "%TARGET%"

echo Installing agentmd.bat shim to %TARGET%
copy /Y "%~dp0agentmd.bat" "%TARGET%\agentmd.bat" >nul

echo Checking PATH...
echo %PATH% | findstr /I /C:"%TARGET%" >nul
if errorlevel 1 (
  echo.
  echo [!] %TARGET% is not in PATH.
  echo     Add it manually:  setx PATH "%%PATH%%;%TARGET%"
  echo     Then open a new terminal.
) else (
  echo OK: %TARGET% already in PATH.
)

echo.
echo Done. Try:  agentmd new "list TODOs in this repo" --agent claude-code
endlocal
