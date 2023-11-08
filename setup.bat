@echo off

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
pause