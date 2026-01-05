"""
Database connection utilities for migration scripts
"""
import os
import sys
import django
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emis.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

# Old database connection settings
OLD_DB = {
    'host': '127.0.0.1',
    'database': 'uvtab_emis',
    'user': 'uvtab_user',
    'password': 'StrongPassword',
    'port': '5432'
}

def get_old_connection():
    """Get connection to old database"""
    return psycopg2.connect(**OLD_DB, cursor_factory=RealDictCursor)

def log(msg):
    """Print timestamped log message"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_old_table_count(table_name):
    """Get count of records in old table"""
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result['count']

def get_old_table_data(table_name, order_by='id'):
    """Get all data from old table"""
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name} ORDER BY {order_by}")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def describe_old_table(table_name):
    """Show columns in old table"""
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    cur.close()
    conn.close()
    return columns
