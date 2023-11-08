REM Download the executable.
curl -o "python_installer.exe" "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"

REM Run the downloaded executable.
start /wait python_installer.exe /quiet InstallAllUsers=0 PrependPath=1

REM Check if the executable ran successfully.
IF %ERRORLEVEL% NEQ 0 (
    echo The executable failed to run.
    exit /b %ERRORLEVEL%
)
pause