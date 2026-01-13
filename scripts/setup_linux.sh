#!/bin/bash
# Setup script for Linux

set -e

echo "Setting up Vulnerability Management System on Linux..."

# Check Python version
python3 --version || { echo "Python 3 is required but not installed."; exit 1; }

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Create logs directory
mkdir -p logs

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Create superuser (optional)
echo "Do you want to create a superuser? (y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ] || [ "$create_superuser" = "Y" ]; then
    python manage.py createsuperuser
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Test the setup
echo "Testing setup..."
python test_setup.py

echo ""
echo "Setup complete!"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  python run_server.py"
echo ""
echo "Or for development:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "To import data:"
echo "  source venv/bin/activate"
echo "  python manage.py import_cpe"
echo "  python manage.py import_cve"
echo "  python manage.py import_linux_cve"
echo ""