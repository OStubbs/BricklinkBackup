@echo off
REM Activate the virtual environment.
CALL venv\Scripts\activate.bat

REM Install the required Python packages from requirements.txt.
pip install -r requirements.txt

REM Deactivate the virtual environment.
CALL venv\Scripts\deactivate.bat

echo #######################
echo Python for Bricklink-Backup has been updated!
echo #######################
pause