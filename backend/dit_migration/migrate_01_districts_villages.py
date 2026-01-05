#!/usr/bin/env python
"""
Migration Script 1: Districts & Villages
Run: python dit_migration/migrate_01_districts_villages.py [--dry-run]
"""
from db_connection import get_old_connection, log, get_old_table_count, describe_old_table
from django.db import transaction

def show_old_structure():
    """Show structure of old tables"""
    print("\n=== Old Table Structure ===")
    print("\neims_district columns:")
    for col in describe_old_table('eims_district'):
        print(f"  {col['column_name']}: {col['data_type']}")
    
    print("\neims_village columns:")
    for col in describe_old_table('eims_village'):
        print(f"  {col['column_name']}: {col['data_type']}")

def count_records():
    """Count records in old tables"""
    print("\n=== Record Counts ===")
    print(f"  eims_district: {get_old_table_count('eims_district')}")
    print(f"  eims_village: {get_old_table_count('eims_village')}")

def migrate_districts(dry_run=False):
    """Migrate districts from old to new database"""
    from configurations.models import District
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_district ORDER BY id")
    rows = cur.fetchall()
    
    log(f"Found {len(rows)} districts in old database")
    
    if dry_run:
        print("\nSample data (first 5):")
        for row in rows[:5]:
            print(f"  ID: {row['id']}, Name: {row.get('district_name', row.get('name', 'N/A'))}")
        cur.close()
        conn.close()
        return
    
    migrated = 0
    errors = []
    
    for row in rows:
        try:
            # Map old field names to new
            name = row.get('district_name') or row.get('name', '')
            
            # Default region - you may need to set this manually or have a mapping
            region = row.get('region', 'central')
            
            District.objects.update_or_create(
                id=row['id'],
                defaults={
                    'name': name,
                    'region': region,
                    'is_active': True,
                }
            )
            migrated += 1
        except Exception as e:
            errors.append(f"District {row['id']}: {e}")
    
    cur.close()
    conn.close()
    
    log(f"✓ Districts migrated: {migrated}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for err in errors[:5]:
            print(f"    {err}")

def migrate_villages(dry_run=False):
    """Migrate villages from old to new database"""
    from configurations.models import Village, District
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_village ORDER BY id")
    rows = cur.fetchall()
    
    log(f"Found {len(rows)} villages in old database")
    
    if dry_run:
        print("\nSample data (first 5):")
        for row in rows[:5]:
            print(f"  ID: {row['id']}, Name: {row.get('village_name', row.get('name', 'N/A'))}, District ID: {row.get('district_id')}")
        cur.close()
        conn.close()
        return
    
    migrated = 0
    skipped = 0
    errors = []
    
    for row in rows:
        try:
            # Get district
            district_id = row.get('district_id')
            if not district_id:
                skipped += 1
                continue
            
            try:
                district = District.objects.get(id=district_id)
            except District.DoesNotExist:
                skipped += 1
                continue
            
            name = row.get('village_name') or row.get('name', '')
            
            Village.objects.update_or_create(
                id=row['id'],
                defaults={
                    'name': name,
                    'district': district,
                    'is_active': True,
                }
            )
            migrated += 1
        except Exception as e:
            errors.append(f"Village {row['id']}: {e}")
    
    cur.close()
    conn.close()
    
    log(f"✓ Villages migrated: {migrated}, skipped: {skipped}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for err in errors[:5]:
            print(f"    {err}")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 1: Districts & Villages")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_structure()
        count_records()
        migrate_districts(dry_run=True)
        migrate_villages(dry_run=True)
    else:
        try:
            with transaction.atomic():
                migrate_districts()
                migrate_villages()
                log("=" * 50)
                log("MIGRATION 1 COMPLETED!")
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
