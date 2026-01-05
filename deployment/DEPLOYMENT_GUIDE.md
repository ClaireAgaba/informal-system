# EMIS Production Deployment Guide

## Overview
This guide covers deploying the EMIS system (Django backend + React frontend) to your production server at `emis.uvtab.go.ug`.

## Architecture
```
Internet → Nginx (Port 443) → {
    /api/* → Gunicorn (Django) → PostgreSQL
    /* → React Static Files
}
```

## Prerequisites
- Ubuntu 20.04+ server
- Root/sudo access
- Domain DNS pointing to server IP
- PostgreSQL installed

---

## Part 1: Initial Server Setup (One-time)

### Step 1: Run Server Setup Script
```bash
# On your server as root
cd /tmp
# Upload setup_server.sh to server
chmod +x setup_server.sh
sudo ./setup_server.sh
```

This installs:
- Python 3, PostgreSQL, Nginx, Node.js
- Creates `deploy` user
- Sets up directories
- Configures firewall

### Step 2: Create Production .env File
```bash
sudo -u deploy nano /var/www/emis/backend/.env
```

```env
SECRET_KEY=generate-a-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=emis.uvtab.go.ug,216.104.197.72

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=emis_db
DB_USER=emis_user
DB_PASSWORD=your_secure_password_here
DB_HOST=localhost
DB_PORT=5432

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@uvtab.go.ug
EMAIL_HOST_PASSWORD=your-email-app-password

# SchoolPay Integration
SCHOOLPAY_ENABLED=True
SCHOOLPAY_API_KEY=your-schoolpay-api-key
SCHOOLPAY_ALLOWED_IPS=schoolpay-server-ip
```

---

## Part 2: Deploy Application Code

### Step 1: Upload Code to Server
```bash
# From your local machine
cd "/home/claire/Desktop/projects/informal system"

# Create tarball (excluding unnecessary files)
tar -czf emis-app.tar.gz \
    --exclude='backend/venv' \
    --exclude='backend/__pycache__' \
    --exclude='backend/*.pyc' \
    --exclude='frontend/node_modules' \
    --exclude='frontend/dist' \
    --exclude='.git' \
    backend/ frontend/ nginx/ deployment/

# Upload to server
scp emis-app.tar.gz deploy@216.104.197.72:/tmp/

# On server
ssh deploy@216.104.197.72
cd /var/www/emis
tar -xzf /tmp/emis-app.tar.gz
```

### Step 2: Set Up Backend
```bash
cd /var/www/emis/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Test Django
python manage.py runserver 0.0.0.0:8000
# Press Ctrl+C after verifying it works
```

### Step 3: Set Up Frontend
```bash
cd /var/www/emis/frontend

# Install dependencies
npm install

# Update API URL for production
# Edit src/services/apiClient.js
nano src/services/apiClient.js
```

Update the baseURL:
```javascript
const apiClient = axios.create({
  baseURL: 'https://emis.uvtab.go.ug/api',  // Production URL
  headers: {
    'Content-Type': 'application/json',
  },
});
```

```bash
# Build production bundle
npm run build

# Verify build created
ls -la dist/
```

### Step 4: Set Up Systemd Service
```bash
# Copy service file
sudo cp /var/www/emis/backend/systemd/emis.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable emis

# Start service
sudo systemctl start emis

# Check status
sudo systemctl status emis
```

### Step 5: Set Up Nginx
```bash
# Copy nginx config
sudo cp /var/www/emis/nginx/emis.conf /etc/nginx/sites-available/emis

# Create symlink
sudo ln -s /etc/nginx/sites-available/emis /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Step 6: Set Up SSL Certificate
```bash
# Install SSL certificate
sudo certbot --nginx -d emis.uvtab.go.ug

# Follow prompts:
# - Enter email address
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (option 2)

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## Part 3: Verify Deployment

### Check Services
```bash
# Check all services are running
sudo systemctl status emis
sudo systemctl status nginx
sudo systemctl status postgresql

# Check logs
sudo journalctl -u emis -n 50
sudo tail -f /var/www/emis/logs/nginx/error.log
```

### Test Application
1. Open browser: `https://emis.uvtab.go.ug`
2. You should see the login page
3. Try logging in with superuser credentials
4. Test creating a candidate
5. Test generating a report

---

## Part 4: Future Deployments (Updates)

### Quick Deployment Script
```bash
# Make deploy script executable
chmod +x /var/www/emis/deployment/deploy.sh

# Run deployment
cd /var/www/emis
./deployment/deploy.sh
```

This script will:
1. Pull latest code (if using git)
2. Install Python dependencies
3. Run migrations
4. Collect static files
5. Build React frontend
6. Restart services

---

## Troubleshooting

### Backend Not Starting
```bash
# Check logs
sudo journalctl -u emis -n 100

# Common issues:
# - Database connection: Check .env credentials
# - Port already in use: sudo lsof -i :8000
# - Permission issues: Check file ownership
```

### Frontend Not Loading
```bash
# Check nginx logs
sudo tail -f /var/www/emis/logs/nginx/error.log

# Verify build exists
ls -la /var/www/emis/frontend/dist/

# Check nginx config
sudo nginx -t
```

### Database Issues
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Connect to database
sudo -u postgres psql emis_db

# Check connections
SELECT * FROM pg_stat_activity WHERE datname = 'emis_db';
```

### SSL Certificate Issues
```bash
# Renew certificate manually
sudo certbot renew

# Check certificate expiry
sudo certbot certificates
```

---

## Performance Optimization

### PostgreSQL Tuning
Edit `/etc/postgresql/*/main/postgresql.conf`:
```conf
# Adjust based on your server RAM
shared_buffers = 512MB          # 25% of RAM
effective_cache_size = 2GB      # 50-75% of RAM
maintenance_work_mem = 128MB
work_mem = 8MB
```

### Nginx Caching
Already configured in `emis.conf`:
- Static assets: 1 year cache
- API responses: No cache
- Media files: 7 days cache

### Gunicorn Workers
Edit `gunicorn_config.py`:
```python
# Formula: (2 x CPU cores) + 1
workers = 9  # For 4 CPU cores
```

---

## Monitoring

### Log Files
```bash
# Application logs
tail -f /var/www/emis/logs/gunicorn/error.log
tail -f /var/www/emis/logs/nginx/access.log

# System logs
sudo journalctl -u emis -f
sudo journalctl -u nginx -f
```

### Disk Space
```bash
# Check disk usage
df -h

# Check log sizes
du -sh /var/www/emis/logs/*
```

### Database Size
```bash
sudo -u postgres psql emis_db -c "
SELECT pg_size_pretty(pg_database_size('emis_db'));
"
```

---

## Backup Strategy

### Database Backup
```bash
# Create backup script
sudo nano /usr/local/bin/backup-emis-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/emis"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
sudo -u postgres pg_dump emis_db | gzip > $BACKUP_DIR/emis_db_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "emis_db_*.sql.gz" -mtime +7 -delete
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/backup-emis-db.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
0 2 * * * /usr/local/bin/backup-emis-db.sh
```

### Media Files Backup
```bash
# Backup uploaded files
tar -czf /var/backups/emis/media_$(date +%Y%m%d).tar.gz \
    /var/www/emis/backend/media/
```

---

## Security Checklist

- [x] DEBUG=False in production
- [x] Strong SECRET_KEY
- [x] SSL certificate installed
- [x] Firewall configured (UFW)
- [x] PostgreSQL not exposed externally
- [x] Regular backups scheduled
- [x] Log rotation configured
- [ ] Set up fail2ban for SSH protection
- [ ] Configure monitoring/alerting
- [ ] Regular security updates

---

## Support Contacts

- Server Admin: deploy@216.104.197.72
- Application URL: https://emis.uvtab.go.ug
- Database: PostgreSQL on localhost:5432

---

## Quick Reference Commands

```bash
# Restart backend
sudo systemctl restart emis

# Restart nginx
sudo systemctl reload nginx

# View logs
sudo journalctl -u emis -f

# Run migrations
cd /var/www/emis/backend
source venv/bin/activate
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```
