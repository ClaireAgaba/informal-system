#!/usr/bin/env python
"""
Migration Script 6: Staff & Support Staff
Run: python dit_migration/migrate_06_staff.py [--dry-run]
"""
from db_connection import get_old_connection, log, get_old_table_count, describe_old_table
from django.db import transaction

def show_old_structure():
    """Show structure of old tables"""
    print("\n=== Old Table Structure ===")
    
    for table in ['eims_staff', 'eims_supportstaff']:
        print(f"\n{table} columns:")
        try:
            for col in describe_old_table(table):
                print(f"  {col['column_name']}: {col['data_type']}")
        except Exception as e:
            print(f"  Error: {e}")

def count_records():
    """Count records in old tables"""
    print("\n=== Record Counts ===")
    try:
        print(f"  eims_staff: {get_old_table_count('eims_staff')}")
    except:
        print("  eims_staff: Table not found")
    try:
        print(f"  eims_supportstaff: {get_old_table_count('eims_supportstaff')}")
    except:
        print("  eims_supportstaff: Table not found")

def migrate_staff(dry_run=False):
    """Migrate staff members"""
    from users.models import Staff, User
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_staff ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} staff in old database")
    
    if dry_run:
        print("\nSample data (first 5):")
        for row in rows[:5]:
            print(f"  ID: {row['id']}, Name: {row.get('name') or row.get('fullname') or row.get('full_name')}, Email: {row.get('email')}")
        return
    
    migrated = 0
    skipped = 0
    
    for row in rows:
        try:
            # Get name from various possible field names
            full_name = row.get('name') or row.get('fullname') or row.get('full_name') or ''
            full_name = full_name[:200]
            
            email = row.get('email') or ''
            if not email:
                skipped += 1
                continue
            
            contact = (row.get('contact') or row.get('phone') or '')[:15]
            account_status = row.get('account_status') or 'active'
            if account_status not in ['active', 'inactive', 'suspended']:
                account_status = 'active'
            
            # Check if staff with this email already exists
            existing = Staff.objects.filter(email=email).first()
            if existing:
                # Update existing
                existing.full_name = full_name
                existing.contact = contact
                existing.account_status = account_status
                existing.save()
            else:
                # Create new staff (without user for now - can be created later)
                Staff.objects.create(
                    id=row['id'],
                    full_name=full_name,
                    email=email,
                    contact=contact,
                    account_status=account_status,
                )
            migrated += 1
            
        except Exception as e:
            log(f"  Error migrating staff {row['id']}: {e}")
            skipped += 1
    
    log(f"✓ Staff migrated: {migrated}, skipped: {skipped}")

def migrate_support_staff(dry_run=False):
    """Migrate support staff members"""
    from users.models import SupportStaff, User
    
    conn = get_old_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM eims_supportstaff ORDER BY id")
        rows = cur.fetchall()
    except Exception as e:
        log(f"Support staff table not found or error: {e}")
        cur.close()
        conn.close()
        return
    
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} support staff in old database")
    
    if dry_run:
        print("\nSample data (first 5):")
        for row in rows[:5]:
            print(f"  ID: {row['id']}, Name: {row.get('name') or row.get('fullname') or row.get('full_name')}, Email: {row.get('email')}")
        return
    
    migrated = 0
    skipped = 0
    
    for row in rows:
        try:
            full_name = row.get('name') or row.get('fullname') or row.get('full_name') or ''
            full_name = full_name[:200]
            
            email = row.get('email') or ''
            if not email:
                skipped += 1
                continue
            
            contact = (row.get('contact') or row.get('phone') or '')[:15]
            account_status = row.get('account_status') or 'active'
            if account_status not in ['active', 'inactive', 'suspended']:
                account_status = 'active'
            
            existing = SupportStaff.objects.filter(email=email).first()
            if existing:
                existing.full_name = full_name
                existing.contact = contact
                existing.account_status = account_status
                existing.save()
            else:
                SupportStaff.objects.create(
                    id=row['id'],
                    full_name=full_name,
                    email=email,
                    contact=contact,
                    account_status=account_status,
                )
            migrated += 1
            
        except Exception as e:
            log(f"  Error migrating support staff {row['id']}: {e}")
            skipped += 1
    
    log(f"✓ Support staff migrated: {migrated}, skipped: {skipped}")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 6: Staff & Support Staff")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_structure()
        count_records()
        migrate_staff(dry_run=True)
        migrate_support_staff(dry_run=True)
    else:
        try:
            with transaction.atomic():
                migrate_staff()
                migrate_support_staff()
                log("=" * 50)
                log("MIGRATION 6 COMPLETED!")
                log("=" * 50)
        except Exception as e:
            log(f"MIGRATION FAILED: {e}")
            raise

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    args = parser.parse_args()
    run(dry_run=args.dry_run)
