#!/usr/bin/env python
"""
Migration Script 4: Assessment Centers & Branches
Run: python dit_migration/migrate_04_assessment_centers.py [--dry-run]
"""
from db_connection import get_old_connection, log, get_old_table_count, describe_old_table
from django.db import transaction

def show_old_structure():
    """Show structure of old tables"""
    print("\n=== Old Table Structure ===")
    
    for table in ['eims_assessmentcenter', 'eims_assessmentcenterbranch']:
        print(f"\n{table} columns:")
        for col in describe_old_table(table):
            print(f"  {col['column_name']}: {col['data_type']}")

def count_records():
    """Count records in old tables"""
    print("\n=== Record Counts ===")
    print(f"  eims_assessmentcenter: {get_old_table_count('eims_assessmentcenter')}")
    print(f"  eims_assessmentcenterbranch: {get_old_table_count('eims_assessmentcenterbranch')}")

def migrate_centers(dry_run=False):
    """Migrate assessment centers"""
    from assessment_centers.models import AssessmentCenter
    from configurations.models import District
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_assessmentcenter ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} assessment centers in old database")
    
    if dry_run:
        print("\nSample data (first 5):")
        for row in rows[:5]:
            print(f"  ID: {row['id']}, Number: {row.get('center_number')}, Name: {row.get('center_name')}")
        return
    
    migrated = 0
    
    for row in rows:
        district = None
        if row.get('district_id'):
            try:
                district = District.objects.get(id=row['district_id'])
            except District.DoesNotExist:
                pass
        
        AssessmentCenter.objects.update_or_create(
            id=row['id'],
            defaults={
                'center_name': row.get('center_name', ''),
                'center_number': row.get('center_number', ''),
                'district': district,
                'address': row.get('address', ''),
                'contact': row.get('contact', ''),
                'email': row.get('email', ''),
                'is_active': row.get('is_active', True),
            }
        )
        migrated += 1
    
    log(f"✓ Assessment centers migrated: {migrated}")

def migrate_branches(dry_run=False):
    """Migrate center branches"""
    from assessment_centers.models import AssessmentCenter, CenterBranch
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_assessmentcenterbranch ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} center branches in old database")
    
    if dry_run:
        print("\nSample data (first 5):")
        for row in rows[:5]:
            # Old DB uses branch_code, no branch_name field
            print(f"  ID: {row['id']}, Center ID: {row.get('assessment_center_id')}, Code: {row.get('branch_code')}")
        return
    
    migrated = 0
    skipped = 0
    
    for row in rows:
        center_id = row.get('assessment_center_id')
        if not center_id:
            skipped += 1
            continue
        
        try:
            center = AssessmentCenter.objects.get(id=center_id)
        except AssessmentCenter.DoesNotExist:
            skipped += 1
            continue
        
        # Old DB has no branch_name, only branch_code - use code as name too
        branch_code = row.get('branch_code') or ''
        branch_name = branch_code or f"Branch {row['id']}"
        
        CenterBranch.objects.update_or_create(
            id=row['id'],
            defaults={
                'assessment_center': center,
                'branch_name': branch_name,
                'branch_code': branch_code,
                'is_active': True,
            }
        )
        migrated += 1
    
    log(f"✓ Center branches migrated: {migrated}, skipped: {skipped}")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 4: Assessment Centers & Branches")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_structure()
        count_records()
        migrate_centers(dry_run=True)
        migrate_branches(dry_run=True)
    else:
        try:
            with transaction.atomic():
                migrate_centers()
                migrate_branches()
                log("=" * 50)
                log("MIGRATION 4 COMPLETED!")
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
