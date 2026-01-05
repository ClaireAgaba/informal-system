#!/usr/bin/env python
"""
Migration Script 2: Sectors & Occupations
- Migrates only NON-old occupations (without -old/-Old in code)
- Creates a mapping file for -old -> non-old occupation IDs
Run: python dit_migration/migrate_02_sectors_occupations.py [--dry-run]
"""
import json
import os
from db_connection import get_old_connection, log, get_old_table_count, describe_old_table
from django.db import transaction

MAPPING_FILE = os.path.join(os.path.dirname(__file__), 'occupation_mapping.json')

def show_old_structure():
    """Show structure of old tables"""
    print("\n=== Old Table Structure ===")
    print("\neims_sector columns:")
    for col in describe_old_table('eims_sector'):
        print(f"  {col['column_name']}: {col['data_type']}")
    
    print("\neims_occupation columns:")
    for col in describe_old_table('eims_occupation'):
        print(f"  {col['column_name']}: {col['data_type']}")

def count_records():
    """Count records in old tables"""
    print("\n=== Record Counts ===")
    print(f"  eims_sector: {get_old_table_count('eims_sector')}")
    print(f"  eims_occupation: {get_old_table_count('eims_occupation')}")

def analyze_occupations():
    """Analyze occupations to identify -old duplicates"""
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_occupation ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    old_codes = []
    non_old_codes = []
    
    for row in rows:
        # Old DB uses 'code' and 'name' fields
        code = row.get('code') or ''
        name = row.get('name') or ''
        if '-old' in code.lower():
            old_codes.append({'id': row['id'], 'code': code, 'name': name})
        else:
            non_old_codes.append({'id': row['id'], 'code': code, 'name': name})
    
    print(f"\n=== Occupation Analysis ===")
    print(f"  Non-old occupations: {len(non_old_codes)} (will migrate)")
    print(f"  Old occupations: {len(old_codes)} (will map to non-old)")
    
    # Try to find mappings
    mapping = {}
    for old in old_codes:
        # Remove -old/-Old from code to find match
        clean_code = old['code'].replace('-Old', '').replace('-old', '')
        for non_old in non_old_codes:
            if non_old['code'] == clean_code:
                mapping[old['id']] = non_old['id']
                break
    
    print(f"  Auto-mapped: {len(mapping)} of {len(old_codes)}")
    
    # Show unmapped
    unmapped = [o for o in old_codes if o['id'] not in mapping]
    if unmapped:
        print(f"\n  Unmapped -old occupations ({len(unmapped)}):")
        for u in unmapped[:10]:
            print(f"    ID {u['id']}: {u['code']} - {u['name']}")
    
    return mapping, old_codes, non_old_codes

def migrate_sectors(dry_run=False):
    """Migrate sectors from old to new database"""
    from occupations.models import Sector
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_sector ORDER BY id")
    rows = cur.fetchall()
    
    log(f"Found {len(rows)} sectors in old database")
    
    if dry_run:
        print("\nSample data (first 5):")
        for row in rows[:5]:
            print(f"  ID: {row['id']}, Name: {row.get('sector_name') or row.get('name')}")
        cur.close()
        conn.close()
        return
    
    migrated = 0
    
    for row in rows:
        name = row.get('sector_name') or row.get('name') or ''
        Sector.objects.update_or_create(
            id=row['id'],
            defaults={
                'name': name,
                'description': row.get('description', ''),
                'is_active': True,
            }
        )
        migrated += 1
    
    cur.close()
    conn.close()
    log(f"✓ Sectors migrated: {migrated}")

def migrate_occupations(dry_run=False):
    """Migrate non-old occupations and create mapping for -old ones"""
    from occupations.models import Occupation, Sector
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_occupation ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} occupations in old database")
    
    # Separate -old and non-old
    old_occs = []
    non_old_occs = []
    
    for row in rows:
        # Old DB uses 'code' and 'name' fields
        code = row.get('code') or ''
        if '-old' in code.lower():
            old_occs.append(row)
        else:
            non_old_occs.append(row)
    
    log(f"  Non-old: {len(non_old_occs)}, Old: {len(old_occs)}")
    
    if dry_run:
        print("\nSample non-old occupations (first 5):")
        for row in non_old_occs[:5]:
            code = row.get('code') or ''
            name = row.get('name') or ''
            print(f"  ID: {row['id']}, Code: {code}, Name: {name}")
        return
    
    # Migrate non-old occupations
    migrated = 0
    for row in non_old_occs:
        # Old DB uses 'code' and 'name' fields
        code = row.get('code') or ''
        name = row.get('name') or ''
        
        sector = None
        if row.get('sector_id'):
            try:
                sector = Sector.objects.get(id=row['sector_id'])
            except Sector.DoesNotExist:
                pass
        
        # Map category_id: 1 = Formal, 2 = Worker's PAS
        category_id = row.get('category_id')
        if category_id == 2:
            category = 'workers_pas'
        else:
            category = 'formal'
        
        Occupation.objects.update_or_create(
            id=row['id'],
            defaults={
                'occ_code': code,
                'occ_name': name,
                'occ_category': category,
                'sector': sector,
                'has_modular': row.get('has_modular', False),
                'is_active': True,
            }
        )
        migrated += 1
    
    log(f"✓ Non-old occupations migrated: {migrated}")
    
    # Create mapping for -old occupations
    mapping = {}
    for old_row in old_occs:
        old_code = old_row.get('code') or ''
        clean_code = old_code.replace('-Old', '').replace('-old', '')
        
        # Find matching non-old occupation
        for non_old_row in non_old_occs:
            non_old_code = non_old_row.get('code') or ''
            if non_old_code == clean_code:
                mapping[str(old_row['id'])] = non_old_row['id']
                break
    
    # Save mapping to file
    with open(MAPPING_FILE, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    log(f"✓ Occupation mapping saved: {len(mapping)} entries -> {MAPPING_FILE}")
    
    unmapped_count = len(old_occs) - len(mapping)
    if unmapped_count > 0:
        log(f"⚠ Unmapped -old occupations: {unmapped_count}")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 2: Sectors & Occupations")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_structure()
        count_records()
        analyze_occupations()
        migrate_sectors(dry_run=True)
        migrate_occupations(dry_run=True)
    else:
        try:
            with transaction.atomic():
                migrate_sectors()
                migrate_occupations()
                log("=" * 50)
                log("MIGRATION 2 COMPLETED!")
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
