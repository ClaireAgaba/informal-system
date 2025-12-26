#!/bin/bash

# EMIS Setup Script

echo "Setting up EMIS (Educational Management Information System)..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Create necessary directories
echo "Creating media and static directories..."
mkdir -p media
mkdir -p static
mkdir -p staticfiles

# Run migrations
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser prompt
echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Create a superuser: python manage.py createsuperuser"
echo "3. Run the development server: python manage.py runserver"
echo ""
