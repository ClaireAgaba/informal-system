#!/usr/bin/env python
"""
Migration Script 8f: Formal Results
Run: python dit_migration/migrate_08f_results_formal.py [--dry-run]

Migrates formal results from eims_result table.
Formal results have level_id set, no module_id.
"""
from db_connection import get_old_connection, log, describe_old_table

def show_old_structure():
    """Show structure of old tables"""
    print("\n=== Old Table Structure ===")
    print("\neims_result columns:")
    try:
        for col in describe_old_table('eims_result'):
            print(f"  {col['column_name']}: {col['data_type']}")
    except Exception as e:
        print(f"  Error: {e}")

def count_records():
    """Count formal results in old table"""
    conn = get_old_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT COUNT(*) as cnt FROM eims_result 
        WHERE result_type = 'formal' AND mark IS NOT NULL
    """)
    total = cur.fetchone()['cnt']
    
    cur.close()
    conn.close()
    
    print("\n=== Record Counts ===")
    print(f"  Formal results with marks: {total}")

def migrate_formal_results(dry_run=False):
    """Migrate formal results"""
    from results.models import FormalResult
    from candidates.models import Candidate
    from assessment_series.models import AssessmentSeries
    from occupations.models import OccupationLevel
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Get existing results to skip
    existing = set(
        FormalResult.objects.values_list('candidate_id', 'assessment_series_id', 'level_id', 'type')
    )
    log(f"Found {len(existing)} existing formal results (will skip)")
    
    # Build level lookup
    levels_by_id = {l.id: l for l in OccupationLevel.objects.all()}
    log(f"Loaded {len(levels_by_id)} levels")
    
    # Get FORMAL results only (result_type = 'formal', has level_id)
    cur.execute("""
        SELECT * FROM eims_result 
        WHERE result_type = 'formal' AND mark IS NOT NULL AND level_id IS NOT NULL
        ORDER BY candidate_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} formal results in old DB")
    
    # Pre-load valid candidates and series
    valid_candidates = set(Candidate.objects.values_list('id', flat=True))
    valid_series = set(AssessmentSeries.objects.values_list('id', flat=True))
    log(f"Valid candidates: {len(valid_candidates)}, Valid series: {len(valid_series)}")
    
    if dry_run:
        print("\nSample results (first 10):")
        for row in rows[:10]:
            print(f"  Candidate: {row['candidate_id']}, Level: {row['level_id']}, "
                  f"Type: {row['assessment_type']}, Mark: {row['mark']}")
        return
    
    created = 0
    skipped = 0
    
    for row in rows:
        try:
            candidate_id = row['candidate_id']
            series_id = row['assessment_series_id']
            level_id = row['level_id']
            mark = row['mark']
            assessment_type = (row.get('assessment_type') or 'practical').lower()
            status = (row.get('status') or 'Normal').lower()
            
            # Map type
            result_type = assessment_type if assessment_type in ['practical', 'theory'] else 'practical'
            result_status = status if status in ['normal', 'retake', 'missing'] else 'normal'
            
            # Get level
            level = levels_by_id.get(level_id)
            if not level:
                skipped += 1
                continue
            
            # Check if exists
            if (candidate_id, series_id, level_id, result_type) in existing:
                skipped += 1
                continue
            
            # Check candidate exists
            if candidate_id not in valid_candidates:
                skipped += 1
                continue
            
            # Check series exists
            if series_id not in valid_series:
                skipped += 1
                continue
            
            # Create result
            FormalResult.objects.create(
                candidate_id=candidate_id,
                assessment_series_id=series_id,
                level=level,
                type=result_type,
                mark=mark,
                status=result_status,
            )
            existing.add((candidate_id, series_id, level_id, result_type))
            created += 1
            
            if created % 5000 == 0:
                log(f"  Progress: {created} results created...")
                
        except Exception as e:
            log(f"  Error: {e}")
            skipped += 1
    
    log(f"✓ Formal results created: {created}, skipped: {skipped}")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 8f: Formal Results")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_structure()
        count_records()
        migrate_formal_results(dry_run=True)
    else:
        migrate_formal_results()
        log("=" * 50)
        log("MIGRATION 8f COMPLETED!")
        log("=" * 50)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    args = parser.parse_args()
    run(dry_run=args.dry_run)
