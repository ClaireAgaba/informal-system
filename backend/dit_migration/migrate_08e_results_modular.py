#!/usr/bin/env python
"""
Migration Script 8e: Modular Results
Run: python dit_migration/migrate_08e_results_modular.py [--dry-run]

Modular results from eims_candidatemodule table:
- candidate_id, module_id, assessment_series_id, marks, status

Creates ModularResult records with mark, grade is auto-calculated.
"""
from db_connection import get_old_connection, log
from django.db import transaction

def show_old_structure():
    """Show structure of old results data"""
    print("\n=== Old Table Structure ===")
    print("\neims_candidatemodule columns (for marks):")
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'eims_candidatemodule'
        ORDER BY ordinal_position
    """)
    for col in cur.fetchall():
        print(f"  {col['column_name']}: {col['data_type']}")
    cur.close()
    conn.close()

def count_records():
    """Count modular results records"""
    print("\n=== Record Counts ===")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) as cnt FROM eims_candidatemodule WHERE marks IS NOT NULL")
    result = cur.fetchone()
    print(f"  Records with marks: {result['cnt'] if result else 0}")
    
    cur.execute("SELECT COUNT(*) as cnt FROM eims_candidatemodule WHERE marks IS NOT NULL AND marks > 0")
    result = cur.fetchone()
    print(f"  Records with marks > 0: {result['cnt'] if result else 0}")
    
    cur.close()
    conn.close()

def migrate_modular_results(dry_run=False, skip_existing=True):
    """Migrate modular results"""
    from results.models import ModularResult
    from candidates.models import Candidate
    from assessment_series.models import AssessmentSeries
    from occupations.models import OccupationModule
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Build module name mapping
    cur.execute("SELECT id, name FROM eims_module")
    old_modules = {row['id']: row['name'] for row in cur.fetchall()}
    log(f"Loaded {len(old_modules)} old module names")
    
    module_mapping = {}
    new_modules_by_name = {m.module_name.strip().lower(): m for m in OccupationModule.objects.all()}
    for old_id, old_name in old_modules.items():
        if old_name:
            clean_name = old_name.strip().lower()
            if clean_name in new_modules_by_name:
                module_mapping[old_id] = new_modules_by_name[clean_name]
    log(f"Mapped {len(module_mapping)} modules by name")
    
    # Get existing results to skip
    existing = set()
    if skip_existing:
        existing = set(
            ModularResult.objects.values_list('candidate_id', 'assessment_series_id', 'module_id', 'type')
        )
        log(f"Found {len(existing)} existing modular results (will skip)")
    
    # Get modular results from old DB (only where marks exist)
    cur.execute("""
        SELECT candidate_id, assessment_series_id, module_id, marks, status
        FROM eims_candidatemodule
        WHERE marks IS NOT NULL AND assessment_series_id IS NOT NULL
        ORDER BY candidate_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} modular results in old DB")
    
    if dry_run:
        print("\nSample results (first 10):")
        for row in rows[:10]:
            module_name = old_modules.get(row['module_id'], 'Unknown')
            print(f"  Candidate {row['candidate_id']}, Series {row['assessment_series_id']}, "
                  f"Module {row['module_id']} ({module_name}), Mark: {row['marks']}")
        return
    
    created = 0
    skipped = 0
    
    for row in rows:
        try:
            candidate_id = row['candidate_id']
            series_id = row['assessment_series_id']
            module_id = row['module_id']
            mark = row['marks']
            status = row.get('status', 'normal')
            
            # Map status
            if status in ['normal', 'retake', 'missing']:
                result_status = status
            elif status == 'completed':
                result_status = 'normal'
            else:
                result_status = 'normal'
            
            # Get module by name mapping
            module = module_mapping.get(module_id)
            if not module:
                skipped += 1
                continue
            
            # Check if exists (practical type - modular is practical)
            if (candidate_id, series_id, module.id, 'practical') in existing:
                skipped += 1
                continue
            
            # Verify candidate exists
            if not Candidate.objects.filter(id=candidate_id).exists():
                skipped += 1
                continue
            
            # Verify series exists
            if not AssessmentSeries.objects.filter(id=series_id).exists():
                skipped += 1
                continue
            
            # Create result (modular is practical type)
            ModularResult.objects.create(
                candidate_id=candidate_id,
                assessment_series_id=series_id,
                module=module,
                type='practical',
                mark=mark,
                status=result_status,
            )
            existing.add((candidate_id, series_id, module.id, 'practical'))
            created += 1
            
            if created % 5000 == 0:
                log(f"  Progress: {created} results created...")
                
        except Exception as e:
            log(f"  Error: {e}")
            skipped += 1
    
    log(f"✓ Modular results created: {created}, skipped: {skipped}")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 8e: Modular Results")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_structure()
        count_records()
        migrate_modular_results(dry_run=True)
    else:
        try:
            with transaction.atomic():
                migrate_modular_results()
                log("=" * 50)
                log("MIGRATION 8e COMPLETED!")
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
