#!/usr/bin/env python
"""
Fix Script: Add missing modular results by joining module name from old DB
Run: python dit_migration/migrate_08e_fix_modular_results.py [--dry-run]

Joins eims_result with eims_module to get module NAME, then matches to new module by name.
Skips results that already exist.
"""
from db_connection import get_old_connection, log
from django.db import transaction

def fix_modular_results(dry_run=False):
    """Add missing modular results by matching module name"""
    from results.models import ModularResult
    from candidates.models import Candidate
    from assessment_series.models import AssessmentSeries
    from occupations.models import OccupationModule
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Get existing results to skip (candidate_id, series_id, module_id, type)
    existing = set(
        ModularResult.objects.values_list('candidate_id', 'assessment_series_id', 'module_id', 'type')
    )
    log(f"Found {len(existing)} existing modular results (will skip)")
    
    # Build new module lookup by name
    new_modules_by_name = {}
    for m in OccupationModule.objects.all():
        clean_name = m.module_name.strip().lower()
        new_modules_by_name[clean_name] = m
    log(f"Loaded {len(new_modules_by_name)} new modules by name")
    
    # Get modular results with module NAME from old DB
    cur.execute("""
        SELECT r.candidate_id, r.assessment_series_id, r.module_id, 
               r.mark, r.assessment_type, r.status,
               m.name as module_name
        FROM eims_result r
        JOIN eims_module m ON r.module_id = m.id
        WHERE r.result_type = 'modular' AND r.mark IS NOT NULL
        ORDER BY r.candidate_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} modular results in old DB")
    
    # Pre-load valid candidates and series
    valid_candidates = set(Candidate.objects.values_list('id', flat=True))
    valid_series = set(AssessmentSeries.objects.values_list('id', flat=True))
    log(f"Valid candidates: {len(valid_candidates)}, Valid series: {len(valid_series)}")
    
    to_add = []
    skipped_no_module = 0
    skipped_exists = 0
    skipped_no_candidate = 0
    skipped_no_series = 0
    
    for row in rows:
        candidate_id = row['candidate_id']
        series_id = row['assessment_series_id']
        module_name = row['module_name']
        mark = row['mark']
        assessment_type = (row.get('assessment_type') or 'practical').lower()
        status = (row.get('status') or 'Normal').lower()
        
        # Map type
        result_type = assessment_type if assessment_type in ['practical', 'theory'] else 'practical'
        result_status = status if status in ['normal', 'retake', 'missing'] else 'normal'
        
        # Find module by name
        if not module_name:
            skipped_no_module += 1
            continue
            
        clean_name = module_name.strip().lower()
        module = new_modules_by_name.get(clean_name)
        
        if not module:
            skipped_no_module += 1
            continue
        
        # Check if exists
        if (candidate_id, series_id, module.id, result_type) in existing:
            skipped_exists += 1
            continue
        
        # Check candidate exists
        if candidate_id not in valid_candidates:
            skipped_no_candidate += 1
            continue
        
        # Check series exists
        if series_id not in valid_series:
            skipped_no_series += 1
            continue
        
        to_add.append({
            'candidate_id': candidate_id,
            'assessment_series_id': series_id,
            'module': module,
            'type': result_type,
            'mark': mark,
            'status': result_status,
        })
        existing.add((candidate_id, series_id, module.id, result_type))
    
    log(f"To add: {len(to_add)}")
    log(f"Skipped - no module match: {skipped_no_module}")
    log(f"Skipped - already exists: {skipped_exists}")
    log(f"Skipped - no candidate: {skipped_no_candidate}")
    log(f"Skipped - no series: {skipped_no_series}")
    
    # Show unmatched module names
    if dry_run and skipped_no_module > 0:
        conn2 = get_old_connection()
        cur2 = conn2.cursor()
        cur2.execute("""
            SELECT DISTINCT m.name as module_name, COUNT(*) as cnt
            FROM eims_result r
            JOIN eims_module m ON r.module_id = m.id
            WHERE r.result_type = 'modular' AND r.mark IS NOT NULL
            GROUP BY m.name
            ORDER BY cnt DESC
            LIMIT 30
        """)
        print("\nTop 30 old module names with result counts:")
        for row in cur2.fetchall():
            name = row['module_name']
            clean = name.strip().lower() if name else ''
            matched = '✓' if clean in new_modules_by_name else '✗'
            print(f"  {matched} {row['module_name']} ({row['cnt']} results)")
        cur2.close()
        conn2.close()
    
    if dry_run:
        print("\nSample to add (first 10):")
        for item in to_add[:10]:
            print(f"  Candidate {item['candidate_id']}, Module {item['module'].module_name}, Mark {item['mark']}")
        return
    
    # Bulk create
    created = 0
    for item in to_add:
        ModularResult.objects.create(**item)
        created += 1
        if created % 5000 == 0:
            log(f"  Progress: {created} results created...")
    
    log(f"✓ Added {created} modular results")

def run(dry_run=False):
    """Run fix"""
    log("=" * 50)
    log("FIX: Modular Results (by module name)")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        fix_modular_results(dry_run=True)
    else:
        fix_modular_results()
        log("=" * 50)
        log("FIX COMPLETED!")
        log("=" * 50)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    args = parser.parse_args()
    run(dry_run=args.dry_run)
