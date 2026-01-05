#!/bin/bash

# EMIS Deployment Script
# This script deploys both Django backend and React frontend to production

set -e  # Exit on error

echo "=========================================="
echo "EMIS Deployment Script"
echo "=========================================="

# Configuration
PROJECT_DIR="/var/www/emis"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
REPO_URL="your-git-repo-url"  # Update this
BRANCH="main"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running as deploy user
if [ "$USER" != "deploy" ]; then
    print_error "This script must be run as the 'deploy' user"
    exit 1
fi

# 1. Pull latest code
print_status "Pulling latest code from repository..."
cd $PROJECT_DIR
# git pull origin $BRANCH  # Uncomment when using git

# 2. Deploy Backend (Django)
print_status "Deploying Django backend..."

cd $BACKEND_DIR

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt --quiet

# Run migrations
print_status "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Restart Gunicorn
print_status "Restarting Gunicorn service..."
sudo systemctl restart emis

# Check if service started successfully
sleep 2
if sudo systemctl is-active --quiet emis; then
    print_status "Gunicorn service is running"
else
    print_error "Gunicorn service failed to start"
    sudo systemctl status emis
    exit 1
fi

# 3. Deploy Frontend (React)
print_status "Deploying React frontend..."

cd $PROJECT_DIR/frontend

# Install dependencies
print_status "Installing Node dependencies..."
npm install --silent

# Build production bundle
print_status "Building React production bundle..."
npm run build

# Copy build to deployment directory
print_status "Copying build files..."
rm -rf $FRONTEND_DIR/dist
cp -r dist $FRONTEND_DIR/

# 4. Reload Nginx
print_status "Reloading Nginx..."
sudo nginx -t && sudo systemctl reload nginx

# 5. Check deployment
print_status "Checking deployment status..."

# Check Gunicorn
if sudo systemctl is-active --quiet emis; then
    print_status "Backend (Gunicorn): Running"
else
    print_error "Backend (Gunicorn): Not running"
fi

# Check Nginx
if sudo systemctl is-active --quiet nginx; then
    print_status "Nginx: Running"
else
    print_error "Nginx: Not running"
fi

# Check PostgreSQL
if sudo systemctl is-active --quiet postgresql; then
    print_status "PostgreSQL: Running"
else
    print_error "PostgreSQL: Not running"
fi

echo ""
echo "=========================================="
print_status "Deployment completed successfully!"
echo "=========================================="
echo ""
echo "Application URL: https://emis.uvtab.go.ug"
echo ""
echo "To view logs:"
echo "  Backend:  sudo journalctl -u emis -f"
echo "  Nginx:    sudo tail -f /var/www/emis/logs/nginx/error.log"
echo ""
