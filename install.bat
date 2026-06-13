@echo off
echo ==============================================
echo   Whisper Web UI - Standalone Installer
echo ==============================================
echo.
echo This will create a Python Virtual Environment and install all required packages.
echo Make sure you have Python 3.10+ installed and added to PATH.
echo.

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip and installing build tools...
python -m pip install --upgrade pip "setuptools<70" wheel

echo Installing openai-whisper without build isolation...
pip install openai-whisper==20240930 --no-build-isolation

echo Installing remaining requirements...
pip install -r requirements.txt

echo.
echo Installation complete! You can now run start.bat
pause
