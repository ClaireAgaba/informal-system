# EMIS Production Deployment - Step by Step Guide

## Overview
We'll deploy the new system alongside the old one, migrate data, then switch the domain.

**Current Setup:**
- Old system: Running on port 80/443 at `emis.uvtab.go.ug`
- New system: Will run on port 8080/8443 temporarily
- After migration: New system takes over 80/443, old system kept as backup

---

## Phase 1: Deploy New System on Temporary Port

### Step 1: SSH into Server
```bash
ssh your-user@216.104.197.72
```

### Step 2: Create Directory Structure
```bash
# Create new system directory
sudo mkdir -p /var/www/emis-new/{backend,frontend,logs/{nginx,gunicorn,django}}
sudo chown -R $USER:$USER /var/www/emis-new
```

### Step 3: Upload Code to Server
**From your local machine (new terminal):**
```bash
cd "/home/claire/Desktop/projects/informal system"

# Create deployment package
tar -czf emis-new.tar.gz \
    --exclude='backend/venv' \
    --exclude='backend/__pycache__' \
    --exclude='backend/*.pyc' \
    --exclude='backend/staticfiles' \
    --exclude='frontend/node_modules' \
    --exclude='frontend/dist' \
    --exclude='.git' \
    backend/ frontend/ nginx/ deployment/

# Upload to server
scp emis-new.tar.gz your-user@216.104.197.72:/tmp/

# Extract on server
ssh your-user@216.104.197.72
cd /var/www/emis-new
tar -xzf /tmp/emis-new.tar.gz
```

### Step 4: Set Up Backend Environment
```bash
cd /var/www/emis-new/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
nano .env
```

**Add to .env:**
```env
SECRET_KEY=your-new-secret-key-here-make-it-long-and-random
DEBUG=False
ALLOWED_HOSTS=emis.uvtab.go.ug,216.104.197.72,localhost

# New Database (separate from old system)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=emis_new_db
DB_USER=emis_new_user
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

### Step 5: Create New PostgreSQL Database
```bash
# Create new database (separate from old system)
sudo -u postgres psql

# In PostgreSQL:
CREATE DATABASE emis_new_db;
CREATE USER emis_new_user WITH PASSWORD 'your_secure_password_here';
ALTER ROLE emis_new_user SET client_encoding TO 'utf8';
ALTER ROLE emis_new_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE emis_new_user SET timezone TO 'Africa/Kampala';
GRANT ALL PRIVILEGES ON DATABASE emis_new_db TO emis_new_user;
\q
```

### Step 6: Run Django Setup
```bash
cd /var/www/emis-new/backend
source venv/bin/activate

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### Step 7: Update Frontend API URL
```bash
nano /var/www/emis-new/frontend/src/services/apiClient.js
```

**Change baseURL to:**
```javascript
const apiClient = axios.create({
  baseURL: 'https://emis.uvtab.go.ug:8443/api',  // Temporary port
  headers: {
    'Content-Type': 'application/json',
  },
});
```

### Step 8: Build React Frontend
```bash
cd /var/www/emis-new/frontend

# Install Node dependencies
npm install

# Build production bundle
npm run build
```

### Step 9: Update Gunicorn Config for New Port
```bash
nano /var/www/emis-new/backend/gunicorn_config.py
```

**Change bind to:**
```python
bind = '127.0.0.1:8000'  # Keep internal port same
```

### Step 10: Create Systemd Service for New System
```bash
sudo nano /etc/systemd/system/emis-new.service
```

**Add:**
```ini
[Unit]
Description=EMIS New System Gunicorn Daemon
After=network.target

[Service]
User=your-username
Group=www-data
WorkingDirectory=/var/www/emis-new/backend
Environment="PATH=/var/www/emis-new/backend/venv/bin"
ExecStart=/var/www/emis-new/backend/venv/bin/gunicorn \
    --config /var/www/emis-new/backend/gunicorn_config.py \
    emis.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable emis-new
sudo systemctl start emis-new
sudo systemctl status emis-new
```

### Step 11: Create Nginx Config for New System (Port 8443)
```bash
sudo nano /etc/nginx/sites-available/emis-new
```

**Add:**
```nginx
# Redirect HTTP to HTTPS
server {
    listen 8080;
    server_name emis.uvtab.go.ug 216.104.197.72;
    return 301 https://$server_name:8443$request_uri;
}

# HTTPS Server
server {
    listen 8443 ssl http2;
    server_name emis.uvtab.go.ug 216.104.197.72;

    # SSL Configuration (use same cert as old system for now)
    ssl_certificate /etc/letsencrypt/live/emis.uvtab.go.ug/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/emis.uvtab.go.ug/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Logs
    access_log /var/www/emis-new/logs/nginx/access.log;
    error_log /var/www/emis-new/logs/nginx/error.log;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Max upload size
    client_max_body_size 10M;

    # Serve React Frontend
    location / {
        root /var/www/emis-new/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Proxy API requests to Django
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Serve Django admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Serve static files
    location /static/ {
        alias /var/www/emis-new/backend/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Serve media files
    location /media/ {
        alias /var/www/emis-new/backend/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/emis-new /etc/nginx/sites-enabled/

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Step 12: Test New System
```bash
# Check services
sudo systemctl status emis-new
sudo systemctl status nginx

# Check logs
sudo journalctl -u emis-new -n 50
tail -f /var/www/emis-new/logs/nginx/error.log
```

**Access new system:**
- URL: `https://emis.uvtab.go.ug:8443`
- Login with superuser credentials
- Test basic functionality

---

## Phase 2: Data Migration

### Step 1: Identify Old Database Connection
```bash
# Find old system's database credentials
# Check old system's .env or settings file
cat /path/to/old/system/.env
```

### Step 2: Create Migration Script
```bash
cd /var/www/emis-new/backend
nano migrate_data.py
```

**Migration script will be created in next steps based on old DB structure**

### Step 3: Analyze Old Database Schema
```bash
# Connect to old database
sudo -u postgres psql old_database_name

# List tables
\dt

# Check key tables structure
\d candidates
\d enrollments
\d results
\d assessment_centers
\d occupations
# etc.

\q
```

### Step 4: Run Migration Script
```bash
cd /var/www/emis-new/backend
source venv/bin/activate

# Dry run first
python migrate_data.py --dry-run

# Actual migration
python migrate_data.py
```

### Step 5: Verify Migrated Data
```bash
# Check record counts
sudo -u postgres psql emis_new_db

SELECT COUNT(*) FROM candidates_candidate;
SELECT COUNT(*) FROM candidates_candidateenrollment;
SELECT COUNT(*) FROM results_formalresult;
SELECT COUNT(*) FROM assessment_assessmentcenter;
# etc.

\q
```

**Test in application:**
- Login to new system: `https://emis.uvtab.go.ug:8443`
- Check candidates list
- Verify enrollments
- Check results
- Test reports

---

## Phase 3: Switch to New System

### Step 1: Put Old System in Maintenance Mode
```bash
# Create maintenance page
sudo nano /var/www/old-system/maintenance.html
```

```html
<!DOCTYPE html>
<html>
<head>
    <title>System Maintenance</title>
    <style>
        body { font-family: Arial; text-align: center; padding: 50px; }
        h1 { color: #333; }
    </style>
</head>
<body>
    <h1>System Upgrade in Progress</h1>
    <p>We're upgrading to a better system. Please wait a few minutes.</p>
</body>
</html>
```

### Step 2: Update Old Nginx to Show Maintenance
```bash
sudo nano /etc/nginx/sites-available/emis-old
```

**Add at top of server block:**
```nginx
location / {
    return 503;
}

error_page 503 /maintenance.html;
location = /maintenance.html {
    root /var/www/old-system;
    internal;
}
```

```bash
sudo systemctl reload nginx
```

### Step 3: Backup Old System
```bash
# Backup old database
sudo -u postgres pg_dump old_database_name | gzip > /var/backups/old_system_$(date +%Y%m%d).sql.gz

# Backup old files
tar -czf /var/backups/old_system_files_$(date +%Y%m%d).tar.gz /var/www/old-system/
```

### Step 4: Switch Nginx Ports
```bash
# Disable old system on 443
sudo rm /etc/nginx/sites-enabled/emis-old

# Update new system to use port 443
sudo nano /etc/nginx/sites-available/emis-new
```

**Change:**
```nginx
# From:
listen 8443 ssl http2;
listen 8080;

# To:
listen 443 ssl http2;
listen 80;
```

```bash
# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### Step 5: Update Frontend API URL to Production
```bash
nano /var/www/emis-new/frontend/src/services/apiClient.js
```

**Change:**
```javascript
const apiClient = axios.create({
  baseURL: 'https://emis.uvtab.go.ug/api',  // Production URL (no port)
  headers: {
    'Content-Type': 'application/json',
  },
});
```

```bash
# Rebuild frontend
cd /var/www/emis-new/frontend
npm run build
```

### Step 6: Final Verification
**Access:** `https://emis.uvtab.go.ug` (no port number)

- ✅ Login works
- ✅ All data visible
- ✅ Reports generate correctly
- ✅ Candidates can be added/edited
- ✅ Results can be entered
- ✅ Center reps have correct permissions

---

## Phase 4: Post-Deployment

### Step 1: Monitor Logs
```bash
# Watch application logs
sudo journalctl -u emis-new -f

# Watch nginx logs
tail -f /var/www/emis-new/logs/nginx/access.log
tail -f /var/www/emis-new/logs/nginx/error.log
```

### Step 2: Keep Old System as Backup
```bash
# Old system remains at /var/www/old-system
# Can be started on different port if needed

# To start old system on port 9000:
sudo nano /etc/nginx/sites-available/emis-old-backup
# Configure on port 9000
```

### Step 3: Set Up Automated Backups
```bash
sudo nano /usr/local/bin/backup-emis-new.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/emis-new"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
sudo -u postgres pg_dump emis_new_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/emis-new/backend/media/

# Keep only last 14 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +14 -delete
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +14 -delete
```

```bash
sudo chmod +x /usr/local/bin/backup-emis-new.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
0 2 * * * /usr/local/bin/backup-emis-new.sh
```

---

## Rollback Plan (If Needed)

If something goes wrong:

```bash
# 1. Stop new system
sudo systemctl stop emis-new

# 2. Re-enable old system
sudo ln -s /etc/nginx/sites-available/emis-old /etc/nginx/sites-enabled/
sudo nano /etc/nginx/sites-available/emis-old
# Remove maintenance mode lines

# 3. Reload nginx
sudo nginx -t
sudo systemctl reload nginx

# 4. Old system is back online
```

---

## Summary

**Timeline:**
1. Deploy new system on port 8443 (1-2 hours)
2. Test new system thoroughly (30 mins)
3. Create and run migration scripts (2-4 hours)
4. Verify migrated data (1 hour)
5. Switch ports (15 mins)
6. Final testing (30 mins)

**Total estimated time:** 5-8 hours

**What we need from you:**
1. Old database credentials
2. Confirmation to proceed with each phase
3. Testing after migration

Ready to start? Let me know and we'll begin with Phase 1!
