#!/usr/bin/env python
"""
Migration Script 3: Occupation Levels, Modules & Papers
Run: python dit_migration/migrate_03_levels_modules_papers.py [--dry-run]
"""
import json
import os
from db_connection import get_old_connection, log, get_old_table_count, describe_old_table
from django.db import transaction

MAPPING_FILE = os.path.join(os.path.dirname(__file__), 'occupation_mapping.json')

def load_occupation_mapping():
    """Load occupation ID mapping (old_id -> new_id for -old occupations)"""
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r') as f:
            return json.load(f)
    return {}

def get_mapped_occupation_id(old_occ_id, mapping):
    """Get the correct occupation ID (handles -old mapping)"""
    str_id = str(old_occ_id)
    if str_id in mapping:
        return mapping[str_id]
    return old_occ_id

def show_old_structure():
    """Show structure of old tables"""
    print("\n=== Old Table Structure ===")
    
    for table in ['eims_occupationlevel', 'eims_module', 'eims_paper']:
        print(f"\n{table} columns:")
        for col in describe_old_table(table):
            print(f"  {col['column_name']}: {col['data_type']}")

def count_records():
    """Count records in old tables"""
    print("\n=== Record Counts ===")
    print(f"  eims_occupationlevel: {get_old_table_count('eims_occupationlevel')}")
    print(f"  eims_module: {get_old_table_count('eims_module')}")
    print(f"  eims_paper: {get_old_table_count('eims_paper')}")

def migrate_levels(dry_run=False):
    """Migrate occupation levels"""
    from occupations.models import OccupationLevel, Occupation
    
    mapping = load_occupation_mapping()
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_occupationlevel ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} occupation levels in old database")
    
    if dry_run:
        print("\nSample data (first 5):")
        for row in rows[:5]:
            print(f"  ID: {row['id']}, Occ ID: {row.get('occupation_id')}, Level: {row.get('level_name')}")
        return
    
    migrated = 0
    skipped = 0
    
    for row in rows:
        old_occ_id = row.get('occupation_id')
        if not old_occ_id:
            skipped += 1
            continue
        
        # Get mapped occupation ID
        occ_id = get_mapped_occupation_id(old_occ_id, mapping)
        
        try:
            occupation = Occupation.objects.get(id=occ_id)
        except Occupation.DoesNotExist:
            skipped += 1
            continue
        
        OccupationLevel.objects.update_or_create(
            id=row['id'],
            defaults={
                'occupation': occupation,
                'level_name': row.get('level_name', ''),
                'structure_type': row.get('structure_type', 'modules'),
                'formal_fee': row.get('formal_fee', 0) or 0,
                'workers_pas_base_fee': row.get('workers_pas_base_fee', 0) or 0,
                'workers_pas_per_module_fee': row.get('workers_pas_per_module_fee', 0) or 0,
                'modular_fee_single_module': row.get('modular_fee_single_module', 0) or 0,
                'modular_fee_double_module': row.get('modular_fee_double_module', 0) or 0,
                'is_active': True,
            }
        )
        migrated += 1
    
    log(f"✓ Occupation levels migrated: {migrated}, skipped: {skipped}")

def migrate_modules(dry_run=False):
    """Migrate occupation modules"""
    from occupations.models import OccupationModule, Occupation, OccupationLevel
    
    mapping = load_occupation_mapping()
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_module ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} modules in old database")
    
    if dry_run:
        print("\nSample data (first 5):")
        for row in rows[:5]:
            print(f"  ID: {row['id']}, Code: {row.get('module_code')}, Name: {row.get('module_name')}")
        return
    
    migrated = 0
    skipped = 0
    
    for row in rows:
        old_occ_id = row.get('occupation_id')
        level_id = row.get('level_id') or row.get('occupation_level_id')
        
        if not old_occ_id:
            skipped += 1
            continue
        
        occ_id = get_mapped_occupation_id(old_occ_id, mapping)
        
        try:
            occupation = Occupation.objects.get(id=occ_id)
        except Occupation.DoesNotExist:
            skipped += 1
            continue
        
        level = None
        if level_id:
            try:
                level = OccupationLevel.objects.get(id=level_id)
            except OccupationLevel.DoesNotExist:
                # Try to get first level of occupation
                level = occupation.levels.first()
        
        if not level:
            level = occupation.levels.first()
            if not level:
                skipped += 1
                continue
        
        OccupationModule.objects.update_or_create(
            id=row['id'],
            defaults={
                'module_code': row.get('module_code', ''),
                'module_name': row.get('module_name', ''),
                'occupation': occupation,
                'level': level,
                'is_active': True,
            }
        )
        migrated += 1
    
    log(f"✓ Modules migrated: {migrated}, skipped: {skipped}")

def migrate_papers(dry_run=False):
    """Migrate occupation papers"""
    from occupations.models import OccupationPaper, Occupation, OccupationLevel, OccupationModule
    
    mapping = load_occupation_mapping()
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_paper ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} papers in old database")
    
    if dry_run:
        print("\nSample data (first 5):")
        for row in rows[:5]:
            print(f"  ID: {row['id']}, Code: {row.get('paper_code')}, Name: {row.get('paper_name')}")
        return
    
    migrated = 0
    skipped = 0
    
    for row in rows:
        old_occ_id = row.get('occupation_id')
        level_id = row.get('level_id') or row.get('occupation_level_id')
        
        if not old_occ_id:
            skipped += 1
            continue
        
        occ_id = get_mapped_occupation_id(old_occ_id, mapping)
        
        try:
            occupation = Occupation.objects.get(id=occ_id)
        except Occupation.DoesNotExist:
            skipped += 1
            continue
        
        level = None
        if level_id:
            try:
                level = OccupationLevel.objects.get(id=level_id)
            except OccupationLevel.DoesNotExist:
                level = occupation.levels.first()
        
        if not level:
            level = occupation.levels.first()
            if not level:
                skipped += 1
                continue
        
        module = None
        if row.get('module_id'):
            try:
                module = OccupationModule.objects.get(id=row['module_id'])
            except OccupationModule.DoesNotExist:
                pass
        
        paper_type = row.get('paper_type', 'theory')
        if paper_type not in ['theory', 'practical']:
            paper_type = 'theory'
        
        OccupationPaper.objects.update_or_create(
            id=row['id'],
            defaults={
                'paper_code': row.get('paper_code', ''),
                'paper_name': row.get('paper_name', ''),
                'occupation': occupation,
                'level': level,
                'module': module,
                'paper_type': paper_type,
                'is_active': True,
            }
        )
        migrated += 1
    
    log(f"✓ Papers migrated: {migrated}, skipped: {skipped}")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 3: Levels, Modules & Papers")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_structure()
        count_records()
        migrate_levels(dry_run=True)
        migrate_modules(dry_run=True)
        migrate_papers(dry_run=True)
    else:
        try:
            with transaction.atomic():
                migrate_levels()
                migrate_modules()
                migrate_papers()
                log("=" * 50)
                log("MIGRATION 3 COMPLETED!")
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
