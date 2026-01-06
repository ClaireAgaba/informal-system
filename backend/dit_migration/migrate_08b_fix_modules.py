#!/usr/bin/env python
"""
Fix Script: Add missing modules to existing modular enrollments
Run: python dit_migration/migrate_08b_fix_modules.py [--dry-run]

This fixes enrollments that were created without modules by matching module names.
"""
from db_connection import get_old_connection, log
from django.db import transaction

def fix_missing_modules(dry_run=False):
    """Add missing modules to existing enrollments using name matching"""
    from candidates.models import Candidate, CandidateEnrollment, EnrollmentModule
    from occupations.models import OccupationModule
    
    # Build module name mapping (old module_id -> new module by name)
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Get old module names - find correct table name first
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%module%'
    """)
    module_tables = [r['table_name'] for r in cur.fetchall()]
    log(f"Found module tables: {module_tables}")
    
    # Try to find the module table with module_name column
    module_table = None
    for t in module_tables:
        try:
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t}'")
            cols = [r['column_name'] for r in cur.fetchall()]
            if 'module_name' in cols:
                module_table = t
                break
        except:
            pass
    
    if not module_table:
        log("Could not find module table with module_name column")
        cur.close()
        conn.close()
        return
    
    log(f"Using module table: {module_table}")
    cur.execute(f"SELECT id, module_name FROM {module_table}")
    old_modules = {row['id']: row['module_name'] for row in cur.fetchall()}
    log(f"Loaded {len(old_modules)} old module names")
    
    # Build mapping: old_module_id -> new OccupationModule (by name match)
    module_mapping = {}
    new_modules_by_name = {m.module_name.strip().lower(): m for m in OccupationModule.objects.all()}
    for old_id, old_name in old_modules.items():
        if old_name:
            clean_name = old_name.strip().lower()
            if clean_name in new_modules_by_name:
                module_mapping[old_id] = new_modules_by_name[clean_name]
    log(f"Mapped {len(module_mapping)} modules by name")
    
    # Get all enrollment-module data from old DB
    cur.execute("""
        SELECT candidate_id, assessment_series_id, module_id
        FROM eims_candidatemodule
        WHERE assessment_series_id IS NOT NULL
        ORDER BY candidate_id
    """)
    old_module_selections = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(old_module_selections)} module selections in old DB")
    
    # Get existing enrollment-module pairs to skip
    existing_pairs = set(
        EnrollmentModule.objects.values_list('enrollment__candidate_id', 'enrollment__assessment_series_id', 'module_id')
    )
    log(f"Found {len(existing_pairs)} existing enrollment-module pairs")
    
    if dry_run:
        # Count how many need to be added
        to_add = 0
        for row in old_module_selections:
            module = module_mapping.get(row['module_id'])
            if module and (row['candidate_id'], row['assessment_series_id'], module.id) not in existing_pairs:
                to_add += 1
        log(f"Would add {to_add} missing module selections")
        return
    
    added = 0
    skipped = 0
    
    for row in old_module_selections:
        try:
            candidate_id = row['candidate_id']
            series_id = row['assessment_series_id']
            old_module_id = row['module_id']
            
            # Get the mapped module
            module = module_mapping.get(old_module_id)
            if not module:
                skipped += 1
                continue
            
            # Check if already exists
            if (candidate_id, series_id, module.id) in existing_pairs:
                skipped += 1
                continue
            
            # Find the enrollment
            try:
                enrollment = CandidateEnrollment.objects.get(
                    candidate_id=candidate_id,
                    assessment_series_id=series_id
                )
            except CandidateEnrollment.DoesNotExist:
                skipped += 1
                continue
            
            # Add the module
            EnrollmentModule.objects.get_or_create(
                enrollment=enrollment,
                module=module
            )
            existing_pairs.add((candidate_id, series_id, module.id))
            added += 1
            
            if added % 5000 == 0:
                log(f"  Progress: {added} modules added...")
                
        except Exception as e:
            log(f"  Error: {e}")
            skipped += 1
    
    log(f"✓ Modules added: {added}, skipped: {skipped}")

def run(dry_run=False):
    """Run fix"""
    log("=" * 50)
    log("FIX: Add missing modules to enrollments")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        fix_missing_modules(dry_run=True)
    else:
        fix_missing_modules()
        log("=" * 50)
        log("FIX COMPLETED!")
        log("=" * 50)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    args = parser.parse_args()
    run(dry_run=args.dry_run)
