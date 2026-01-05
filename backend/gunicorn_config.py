"""
Gunicorn configuration file for EMIS production deployment
"""
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "/var/www/emis/logs/gunicorn/access.log"
errorlog = "/var/www/emis/logs/gunicorn/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "emis_gunicorn"

# Server mechanics
daemon = False
pidfile = "/var/www/emis/backend/gunicorn.pid"
user = "deploy"
group = "deploy"
tmp_upload_dir = None

# SSL (if terminating SSL at Gunicorn level - not recommended, use Nginx)
# keyfile = None
# certfile = None
