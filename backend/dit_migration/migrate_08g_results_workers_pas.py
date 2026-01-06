#!/usr/bin/env python
"""
Migration Script 8g: Workers PAS Results
Run: python dit_migration/migrate_08g_results_workers_pas.py [--dry-run]

Migrates Workers PAS results from eims_result table.
Workers PAS results have level_id, module_id, and paper_id set.
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
    """Count workers pas results in old table"""
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Try different possible values for result_type
    for rt in ['workers_pas', 'workers pas', 'informal', 'Informal']:
        cur.execute(f"SELECT COUNT(*) as cnt FROM eims_result WHERE result_type = '{rt}'")
        cnt = cur.fetchone()['cnt']
        if cnt > 0:
            print(f"  result_type='{rt}': {cnt}")
    
    cur.close()
    conn.close()

def migrate_workers_pas_results(dry_run=False):
    """Migrate workers PAS results"""
    from results.models import WorkersPasResult
    from candidates.models import Candidate
    from assessment_series.models import AssessmentSeries
    from occupations.models import OccupationLevel, OccupationModule, OccupationPaper
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Get existing results to skip
    existing = set(
        WorkersPasResult.objects.values_list('candidate_id', 'assessment_series_id', 'paper_id')
    )
    log(f"Found {len(existing)} existing workers PAS results (will skip)")
    
    # Build lookups by ID and name
    levels_by_id = {l.id: l for l in OccupationLevel.objects.all()}
    levels_by_name = {l.level_name.strip().lower(): l for l in OccupationLevel.objects.all()}
    
    modules_by_id = {m.id: m for m in OccupationModule.objects.all()}
    modules_by_name = {m.module_name.strip().lower(): m for m in OccupationModule.objects.all()}
    
    papers_by_id = {p.id: p for p in OccupationPaper.objects.all()}
    papers_by_name = {p.paper_name.strip().lower(): p for p in OccupationPaper.objects.all()}
    
    log(f"Loaded {len(levels_by_id)} levels, {len(modules_by_id)} modules, {len(papers_by_id)} papers")
    
    # Get old names for mapping
    cur.execute("SELECT id, name FROM eims_level")
    old_levels = {row['id']: row['name'] for row in cur.fetchall()}
    
    cur.execute("SELECT id, name FROM eims_module")
    old_modules = {row['id']: row['name'] for row in cur.fetchall()}
    
    cur.execute("SELECT id, name FROM eims_paper")
    old_papers = {row['id']: row['name'] for row in cur.fetchall()}
    
    log(f"Loaded {len(old_levels)} old levels, {len(old_modules)} old modules, {len(old_papers)} old papers")
    
    # Get Workers PAS results (try different result_type values)
    cur.execute("""
        SELECT * FROM eims_result 
        WHERE result_type IN ('workers_pas', 'workers pas', 'informal', 'Informal')
          AND mark IS NOT NULL 
          AND level_id IS NOT NULL 
          AND paper_id IS NOT NULL
        ORDER BY candidate_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} workers PAS results in old DB")
    
    # Pre-load valid candidates and series
    valid_candidates = set(Candidate.objects.values_list('id', flat=True))
    valid_series = set(AssessmentSeries.objects.values_list('id', flat=True))
    log(f"Valid candidates: {len(valid_candidates)}, Valid series: {len(valid_series)}")
    
    if dry_run:
        print("\nSample results (first 10):")
        for row in rows[:10]:
            print(f"  Candidate: {row['candidate_id']}, Level: {row['level_id']}, "
                  f"Module: {row.get('module_id')}, Paper: {row['paper_id']}, Mark: {row['mark']}")
        return
    
    created = 0
    skipped_no_level = 0
    skipped_no_module = 0
    skipped_no_paper = 0
    skipped_exists = 0
    skipped_no_candidate = 0
    skipped_no_series = 0
    skipped_error = 0
    
    for row in rows:
        try:
            candidate_id = row['candidate_id']
            series_id = row['assessment_series_id']
            level_id = row['level_id']
            module_id = row.get('module_id')
            paper_id = row['paper_id']
            mark = row['mark']
            status = (row.get('status') or 'Normal').lower()
            result_status = status if status in ['normal', 'retake', 'missing'] else 'normal'
            
            # Get level - try by ID then by name
            level = levels_by_id.get(level_id)
            if not level:
                old_name = old_levels.get(level_id, '')
                level = levels_by_name.get(old_name.strip().lower())
            if not level:
                skipped_no_level += 1
                continue
            
            # Get paper - try by ID then by name
            paper = papers_by_id.get(paper_id)
            if not paper:
                old_name = old_papers.get(paper_id, '')
                paper = papers_by_name.get(old_name.strip().lower())
            if not paper:
                skipped_no_paper += 1
                continue
            
            # Get module - try by ID then by name, or use paper's module
            module = None
            if module_id:
                module = modules_by_id.get(module_id)
                if not module:
                    old_name = old_modules.get(module_id, '')
                    module = modules_by_name.get(old_name.strip().lower())
            if not module:
                # Try to get module from paper
                module = paper.module if hasattr(paper, 'module') else None
            if not module:
                skipped_no_module += 1
                continue
            
            # Check if exists
            if (candidate_id, series_id, paper.id) in existing:
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
            
            # Create result
            WorkersPasResult.objects.create(
                candidate_id=candidate_id,
                assessment_series_id=series_id,
                level=level,
                module=module,
                paper=paper,
                mark=mark,
                status=result_status,
            )
            existing.add((candidate_id, series_id, paper.id))
            created += 1
            
            if created % 5000 == 0:
                log(f"  Progress: {created} results created...")
                
        except Exception as e:
            log(f"  Error: {e}")
            skipped_error += 1
    
    log(f"✓ Workers PAS results created: {created}")
    log(f"  Skipped - no level: {skipped_no_level}")
    log(f"  Skipped - no module: {skipped_no_module}")
    log(f"  Skipped - no paper: {skipped_no_paper}")
    log(f"  Skipped - exists: {skipped_exists}")
    log(f"  Skipped - no candidate: {skipped_no_candidate}")
    log(f"  Skipped - no series: {skipped_no_series}")
    log(f"  Skipped - error: {skipped_error}")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 8g: Workers PAS Results")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_structure()
        count_records()
        migrate_workers_pas_results(dry_run=True)
    else:
        migrate_workers_pas_results()
        log("=" * 50)
        log("MIGRATION 8g COMPLETED!")
        log("=" * 50)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    args = parser.parse_args()
    run(dry_run=args.dry_run)
