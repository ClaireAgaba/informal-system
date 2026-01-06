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
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    print("\neims_result columns:")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'eims_result'
        ORDER BY ordinal_position
    """)
    for col in cur.fetchall():
        print(f"  {col['column_name']}: {col['data_type']}")
    
    cur.close()
    conn.close()

def count_records():
    """Count results records"""
    print("\n=== Record Counts ===")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) as cnt FROM eims_result")
    result = cur.fetchone()
    print(f"  Total eims_result: {result['cnt'] if result else 0}")
    
    cur.execute("SELECT COUNT(*) as cnt FROM eims_result WHERE mark IS NOT NULL")
    result = cur.fetchone()
    print(f"  Records with marks: {result['cnt'] if result else 0}")
    
    # Check what columns exist to understand structure
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'eims_result'
    """)
    cols = [r['column_name'] for r in cur.fetchall()]
    print(f"  Columns: {cols}")
    
    cur.close()
    conn.close()

def migrate_modular_results(dry_run=False, skip_existing=True):
    """Migrate modular results from eims_result table"""
    from results.models import ModularResult
    from candidates.models import Candidate
    from assessment_series.models import AssessmentSeries
    from occupations.models import OccupationModule
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # First check the eims_result structure
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'eims_result'
    """)
    cols = [r['column_name'] for r in cur.fetchall()]
    log(f"eims_result columns: {cols}")
    
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
    
    # Determine column names based on what exists
    candidate_col = 'candidate_id' if 'candidate_id' in cols else 'candidate'
    series_col = 'assessment_series_id' if 'assessment_series_id' in cols else 'series_id'
    module_col = 'module_id' if 'module_id' in cols else 'module'
    
    # Get results from eims_result - join with candidate to filter modular only
    query = f"""
        SELECT r.*, c.registration_category
        FROM eims_result r
        JOIN eims_candidate c ON r.{candidate_col} = c.id
        WHERE r.mark IS NOT NULL
        ORDER BY r.{candidate_col}
    """
    
    try:
        cur.execute(query)
        rows = cur.fetchall()
    except Exception as e:
        log(f"Query error: {e}")
        # Try simpler query
        cur.execute(f"SELECT * FROM eims_result WHERE mark IS NOT NULL ORDER BY id LIMIT 10")
        rows = cur.fetchall()
        if rows:
            log(f"Sample row keys: {rows[0].keys()}")
    
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} results in eims_result")
    
    if dry_run:
        print("\nSample results (first 10):")
        for row in rows[:10]:
            print(f"  {dict(row)}")
        return
    
    created = 0
    skipped = 0
    
    for row in rows:
        try:
            candidate_id = row.get('candidate_id') or row.get('candidate')
            series_id = row.get('assessment_series_id') or row.get('series_id')
            module_id = row.get('module_id') or row.get('module')
            mark = row.get('mark')
            
            if not all([candidate_id, series_id, module_id, mark is not None]):
                skipped += 1
                continue
            
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
                status='normal',
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
