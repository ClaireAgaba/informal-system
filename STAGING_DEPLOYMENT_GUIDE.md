# Staging Environment Deployment Guide

**Purpose:** Deploy a staging copy of the Informal System at `staging-emis.uvtab.go.ug` for SchoolPay integration testing.

**Server:** 216.104.197.72

---

## Step 1: Clone the repo to a staging directory

SSH into the server and clone:

```bash
ssh deploy@216.104.197.72

# Clone repo to staging directory
cd /home/deploy
git clone https://github.com/ClaireAgaba/informal-system.git informal-system-staging
```

---

## Step 2: Set up the backend (Python/Django)

```bash
cd /home/deploy/informal-system-staging/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 3: Create the staging .env file

```bash
nano /home/deploy/informal-system-staging/backend/.env
```

Paste this (uses a separate SQLite database so production data is untouched):

```env
SECRET_KEY=staging-secret-key-change-this-to-something-random
DEBUG=False
ALLOWED_HOSTS=staging-emis.uvtab.go.ug,127.0.0.1,localhost

# Staging uses its own SQLite database (completely separate from production)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=/home/deploy/informal-system-staging/backend/db_staging.sqlite3

# SchoolPay Integration - ENABLED for testing
SCHOOLPAY_ENABLED=True
SCHOOLPAY_API_KEY=ECMPceVL4iYPYvwGrBKUqtcbzOmJi9YJuYI7Nio-vAY
SCHOOLPAY_ALLOWED_IPS=
```

> **Note:** Leave `SCHOOLPAY_ALLOWED_IPS` empty for now (disables IP restriction). Once SchoolPay gives you their server IPs, add them as comma-separated values.

---

## Step 4: Initialize the staging database and create test data

```bash
cd /home/deploy/informal-system-staging/backend
source venv/bin/activate

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create a superuser for admin access
python manage.py createsuperuser

# Create test data for SchoolPay testing
python manage.py shell
```

In the Django shell, run:

```python
from candidates.models import Candidate
from assessment_centers.models import AssessmentCenter
from assessment_series.models import AssessmentSeries
from decimal import Decimal

# Create a test assessment center (center 999)
center, _ = AssessmentCenter.objects.get_or_create(
    center_number='UVT0001',
    defaults={'center_name': 'Test Assessment Center', 'district': 'Kampala'}
)

# Create test candidates with known payment codes
# You may need to adjust fields based on required model fields
# Check what fields are required first:
# print([f.name for f in Candidate._meta.get_fields() if hasattr(f, 'null') and not f.null and not f.has_default()])

print("Test center created:", center)
print("Now create test candidates via the admin panel at /admin/")
print("Set payment_code to: IUV000125000001, IUV000125000002, IUV000125000003")
```

> **Tip:** It may be easier to create the test candidates through the Django admin panel at `https://staging-emis.uvtab.go.ug/admin/` after deployment is complete.

---

## Step 5: Create systemd service for staging

```bash
sudo nano /etc/systemd/system/emis-informal-staging.service
```

Paste:

```ini
[Unit]
Description=UVTAB Informal System - Staging
After=network.target

[Service]
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/informal-system-staging/backend
ExecStart=/home/deploy/informal-system-staging/backend/venv/bin/gunicorn emis.wsgi:application --bind 127.0.0.1:8004 --workers 2
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable emis-informal-staging
sudo systemctl start emis-informal-staging
sudo systemctl status emis-informal-staging
```

---

## Step 6: Build the frontend

```bash
cd /home/deploy/informal-system-staging/frontend
npm install
npm run build
```

---

## Step 7: Configure nginx for staging

```bash
sudo nano /etc/nginx/sites-available/emis-informal-staging
```

Paste:

```nginx
server {
    listen 80;
    server_name staging-emis.uvtab.go.ug;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name staging-emis.uvtab.go.ug;

    # Use same SSL certs or get new ones via certbot
    ssl_certificate /etc/letsencrypt/live/staging-emis.uvtab.go.ug/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/staging-emis.uvtab.go.ug/privkey.pem;

    # Logs
    access_log /home/deploy/informal-system-staging/logs/nginx-access.log;
    error_log /home/deploy/informal-system-staging/logs/nginx-error.log;

    # Frontend (React)
    root /home/deploy/informal-system-staging/frontend/dist;
    index index.html;

    # API and Admin proxy to staging gunicorn
    location /api/ {
        proxy_pass http://127.0.0.1:8004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:8004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Serve static and media files
    location /static/ {
        alias /home/deploy/informal-system-staging/backend/staticfiles/;
    }

    location /media/ {
        alias /home/deploy/informal-system-staging/backend/media/;
    }

    # React SPA - all other routes
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Enable the site and get SSL cert:

```bash
# Create logs directory
mkdir -p /home/deploy/informal-system-staging/logs

# Enable site
sudo ln -s /etc/nginx/sites-available/emis-informal-staging /etc/nginx/sites-enabled/

# First, add DNS A record for staging-emis.uvtab.go.ug pointing to 216.104.197.72
# Then get SSL certificate:
sudo certbot certonly --nginx -d staging-emis.uvtab.go.ug

# Test and reload nginx
sudo nginx -t
sudo systemctl reload nginx
```

---

## Step 8: Update production .env for SchoolPay

On the **production** system, add SchoolPay settings:

```bash
nano /home/deploy/informal-system/backend/.env
```

Add these lines:

```env
# SchoolPay Integration
SCHOOLPAY_ENABLED=True
SCHOOLPAY_API_KEY=ECMPceVL4iYPYvwGrBKUqtcbzOmJi9YJuYI7Nio-vAY
SCHOOLPAY_ALLOWED_IPS=
```

Then restart production:

```bash
sudo systemctl restart emis-informal
```

---

## Step 9: DNS Setup

Ask your DNS administrator to create an **A record**:

| Type | Name | Value |
|------|------|-------|
| A | staging-emis.uvtab.go.ug | 216.104.197.72 |

---

## Step 10: Verify everything works

```bash
# Test staging connection
curl -X GET https://staging-emis.uvtab.go.ug/api/candidates/payments/schoolpay/test/ \
  -H "X-API-Key: ECMPceVL4iYPYvwGrBKUqtcbzOmJi9YJuYI7Nio-vAY"

# Expected response:
# {"success": true, "message": "Connection successful", "system": "UVTAB Informal System", "version": "1.0"}
```

---

## Quick Reference

| Item | Value |
|------|-------|
| **Staging URL** | https://staging-emis.uvtab.go.ug |
| **Staging API** | https://staging-emis.uvtab.go.ug/api/candidates/payments/schoolpay |
| **Production URL** | https://emis.uvtab.go.ug |
| **Production API** | https://emis.uvtab.go.ug/api/candidates/payments/schoolpay |
| **API Key** | ECMPceVL4iYPYvwGrBKUqtcbzOmJi9YJuYI7Nio-vAY |
| **Staging Backend Port** | 8004 |
| **Production Backend Port** | 8003 |
| **Staging Service** | emis-informal-staging.service |
| **Production Service** | emis-informal.service |
