@echo off
title Xlink Kai Port Opener
color 0A
echo.
echo  ============================================
echo   Xlink Kai Port Opener - Starting up...
echo  ============================================
echo.

:: ── Check if Python is already installed ─────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo  [OK] Python is already installed.
    goto RUN
)

:: Also check py launcher
py --version >nul 2>&1
if %errorlevel% == 0 (
    echo  [OK] Python launcher found.
    goto RUN_PY
)

:: ── Python not found - download and install silently ─────────────────────────
echo  [..] Python not found. Downloading Python installer...
echo       This only happens once. Please wait...
echo.

:: Check if curl is available (Windows 10+)
curl --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [!!] curl not found. Trying PowerShell download instead...
    goto DOWNLOAD_PS
)

:: Download Python 3.11 embedded/installer using curl
curl -L -o "%TEMP%\python_installer.exe" "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" --progress-bar
if %errorlevel% neq 0 goto DOWNLOAD_PS
goto INSTALL

:DOWNLOAD_PS
echo  [..] Downloading via PowerShell...
powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe'}"
if %errorlevel% neq 0 (
    echo.
    echo  [!!] Download failed. Please install Python manually:
    echo       https://www.python.org/downloads/
    echo       Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

:INSTALL
echo.
echo  [..] Installing Python silently (this may take 1-2 minutes)...
echo       A progress window may appear briefly - this is normal.
echo.

:: Silent install with PATH added, for all users
"%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=0

if %errorlevel% neq 0 (
    echo  [!!] Silent install failed. Trying interactive install...
    "%TEMP%\python_installer.exe"
)

:: Refresh PATH in this session
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "PATH=%%b;%PATH%"
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "PATH=%%b;%PATH%"

:: Verify install worked
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo  [OK] Python installed successfully.
    goto RUN
)

py --version >nul 2>&1
if %errorlevel% == 0 (
    echo  [OK] Python installed successfully.
    goto RUN_PY
)

echo.
echo  [!!] Python installed but PATH not updated yet.
echo       Please close this window and double-click the .bat file again.
echo.
pause
exit /b 1

:: ── Run the script ────────────────────────────────────────────────────────────
:RUN
echo  [OK] Launching Xlink Kai Port Opener...
echo.
python "%~dp0xlink_upnp_opener.py"
if %errorlevel% neq 0 (
    echo.
    echo  [!!] Script failed to run. Error code: %errorlevel%
    echo       Make sure xlink_upnp_opener.py is in the same folder as this .bat file.
    pause
)
exit /b 0

:RUN_PY
echo  [OK] Launching Xlink Kai Port Opener...
echo.
py "%~dp0xlink_upnp_opener.py"
if %errorlevel% neq 0 (
    echo.
    echo  [!!] Script failed to run. Error code: %errorlevel%
    echo       Make sure xlink_upnp_opener.py is in the same folder as this .bat file.
    pause
)
exit /b 0
