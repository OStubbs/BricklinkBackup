@echo off

REM Download the executable.
curl -o "python_installer.exe" "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"

REM Run the downloaded executable.
start /wait python_installer.exe /quiet InstallAllUsers=0 PrependPath=1

echo #######################
echo Python has been installed! 
echo #######################

REM Create a Python virtual environment named 'venv' in the current directory.
python -m venv venv

REM Activate the virtual environment.
CALL venv\Scripts\activate.bat

REM Install the required Python packages from requirements.txt.
pip install -r requirements.txt

REM Deactivate the virtual environment.
CALL venv\Scripts\deactivate.bat

echo #######################
echo Bricklink-Backup has been setup!
echo #######################

pause