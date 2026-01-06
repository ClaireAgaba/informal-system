#!/usr/bin/env python
"""
Migration Script 5: Assessment Series
Run: python dit_migration/migrate_05_assessment_series.py [--dry-run]
"""
from db_connection import get_old_connection, log, get_old_table_count, describe_old_table
from django.db import transaction

def show_old_structure():
    """Show structure of old tables"""
    print("\n=== Old Table Structure ===")
    print("\neims_assessmentseries columns:")
    for col in describe_old_table('eims_assessmentseries'):
        print(f"  {col['column_name']}: {col['data_type']}")

def count_records():
    """Count records in old tables"""
    print("\n=== Record Counts ===")
    print(f"  eims_assessmentseries: {get_old_table_count('eims_assessmentseries')}")

def migrate_series(dry_run=False):
    """Migrate assessment series"""
    from assessment_series.models import AssessmentSeries
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_assessmentseries ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} assessment series in old database")
    
    if dry_run:
        print("\nSample data (first 5):")
        for row in rows[:5]:
            # Old DB uses 'name' and 'is_current' fields
            print(f"  ID: {row['id']}, Name: {row.get('name')}, Current: {row.get('is_current')}")
        return
    
    migrated = 0
    
    for row in rows:
        # Old DB uses 'name' instead of 'series_name', 'is_current' instead of 'is_active'
        series_name = (row.get('name') or '')[:200]
        
        AssessmentSeries.objects.update_or_create(
            id=row['id'],
            defaults={
                'series_name': series_name,
                'start_date': row.get('start_date'),
                'end_date': row.get('end_date'),
                'is_active': row.get('is_current', False),
            }
        )
        migrated += 1
    
    log(f"✓ Assessment series migrated: {migrated}")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 5: Assessment Series")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_structure()
        count_records()
        migrate_series(dry_run=True)
    else:
        try:
            with transaction.atomic():
                migrate_series()
                log("=" * 50)
                log("MIGRATION 5 COMPLETED!")
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
