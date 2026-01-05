#!/bin/bash

# EMIS Server Initial Setup Script
# Run this script once on a fresh server to set up the environment

set -e

echo "=========================================="
echo "EMIS Server Setup Script"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# 1. Update system
echo "[1/10] Updating system packages..."
apt-get update
apt-get upgrade -y

# 2. Install required packages
echo "[2/10] Installing required packages..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl \
    supervisor \
    certbot \
    python3-certbot-nginx

# 3. Install Node.js (for React build)
echo "[3/10] Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# 4. Create deploy user
echo "[4/10] Creating deploy user..."
if id "deploy" &>/dev/null; then
    echo "User 'deploy' already exists"
else
    useradd -m -s /bin/bash deploy
    echo "User 'deploy' created"
fi

# 5. Create project directories
echo "[5/10] Creating project directories..."
mkdir -p /var/www/emis/{backend,frontend,logs/{nginx,gunicorn,django}}
chown -R deploy:deploy /var/www/emis

# 6. Set up PostgreSQL
echo "[6/10] Setting up PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE emis_db;" 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "CREATE USER emis_user WITH PASSWORD 'your_secure_password';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "ALTER ROLE emis_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE emis_user SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE emis_user SET timezone TO 'Africa/Kampala';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE emis_db TO emis_user;"

# 7. Configure PostgreSQL for better performance
echo "[7/10] Optimizing PostgreSQL configuration..."
PG_CONF="/etc/postgresql/*/main/postgresql.conf"
cp $PG_CONF ${PG_CONF}.backup

# These are conservative settings - adjust based on your server specs
cat >> $PG_CONF << EOF

# EMIS Performance Tuning
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
max_connections = 200
EOF

systemctl restart postgresql

# 8. Set up firewall
echo "[8/10] Configuring firewall..."
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw --force enable

# 9. Create log rotation config
echo "[9/10] Setting up log rotation..."
cat > /etc/logrotate.d/emis << EOF
/var/www/emis/logs/*/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
    sharedscripts
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
        systemctl reload emis > /dev/null 2>&1 || true
    endscript
}
EOF

# 10. Set up SSL certificate (Let's Encrypt)
echo "[10/10] Setting up SSL certificate..."
echo "Note: Make sure DNS is pointing to this server before running certbot"
echo "Run manually: sudo certbot --nginx -d emis.uvtab.go.ug"

echo ""
echo "=========================================="
echo "Server setup completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Copy your application code to /var/www/emis/"
echo "2. Set up .env file in /var/www/emis/backend/"
echo "3. Install Python dependencies in virtual environment"
echo "4. Copy systemd service file: sudo cp /var/www/emis/backend/systemd/emis.service /etc/systemd/system/"
echo "5. Copy nginx config: sudo cp /var/www/emis/nginx/emis.conf /etc/nginx/sites-available/emis"
echo "6. Enable nginx site: sudo ln -s /etc/nginx/sites-available/emis /etc/nginx/sites-enabled/"
echo "7. Run SSL setup: sudo certbot --nginx -d emis.uvtab.go.ug"
echo "8. Enable and start services:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable emis"
echo "   sudo systemctl start emis"
echo "   sudo systemctl reload nginx"
echo ""
echo "PostgreSQL Database Credentials:"
echo "  Database: emis_db"
echo "  User: emis_user"
echo "  Password: your_secure_password (CHANGE THIS!)"
echo ""
