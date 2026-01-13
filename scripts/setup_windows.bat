@echo off
REM Setup script for Windows

echo Setting up Vulnerability Management System on Windows...

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is required but not installed.
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing Python dependencies...
pip install -r requirements.txt

REM Copy environment file
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo Please edit .env file with your configuration
)

REM Run migrations
echo Running database migrations...
python manage.py migrate

REM Create superuser (optional)
set /p create_superuser="Do you want to create a superuser? (y/n): "
if /i "%create_superuser%"=="y" (
    python manage.py createsuperuser
)

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

echo.
echo Setup complete!
echo.
echo To start the server:
echo   venv\Scripts\activate.bat
echo   python run_server.py
echo.
echo Or for development:
echo   venv\Scripts\activate.bat
echo   python manage.py runserver
echo.
echo To import data:
echo   venv\Scripts\activate.bat
echo   python manage.py import_cpe
echo   python manage.py import_cve
echo   python manage.py import_linux_cve
echo.
pause