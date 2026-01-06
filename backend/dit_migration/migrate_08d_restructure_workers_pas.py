#!/usr/bin/env python
"""
Restructure Workers PAS: Create separate enrollment per (candidate, series, level)
Run: python dit_migration/migrate_08d_restructure_workers_pas.py [--dry-run]

Workers PAS candidates can be enrolled in multiple levels in the same series.
Each level has its own modules and papers.
This creates separate CandidateEnrollment for each level.
"""
from db_connection import get_old_connection, log
from django.db import transaction

def restructure_workers_pas(dry_run=False):
    """Restructure Workers PAS to have separate enrollment per level"""
    from candidates.models import Candidate, CandidateEnrollment, EnrollmentModule, EnrollmentPaper
    from assessment_series.models import AssessmentSeries
    from occupations.models import OccupationLevel, OccupationModule, OccupationPaper
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Build level name mapping
    old_levels = {}
    for t in ['eims_level']:
        try:
            cur.execute(f"SELECT id, name FROM {t}")
            old_levels = {row['id']: row['name'] for row in cur.fetchall()}
            log(f"Loaded {len(old_levels)} old level names")
            break
        except:
            pass
    
    level_mapping = {}
    new_levels_by_name = {l.level_name.strip().lower(): l for l in OccupationLevel.objects.all()}
    for old_id, old_name in old_levels.items():
        if old_name:
            clean_name = old_name.strip().lower()
            if clean_name in new_levels_by_name:
                level_mapping[old_id] = new_levels_by_name[clean_name]
    log(f"Mapped {len(level_mapping)} levels by name")
    
    # Build module name mapping
    cur.execute("SELECT id, name FROM eims_module")
    old_modules = {row['id']: row['name'] for row in cur.fetchall()}
    
    module_mapping = {}
    new_modules_by_name = {m.module_name.strip().lower(): m for m in OccupationModule.objects.all()}
    for old_id, old_name in old_modules.items():
        if old_name:
            clean_name = old_name.strip().lower()
            if clean_name in new_modules_by_name:
                module_mapping[old_id] = new_modules_by_name[clean_name]
    log(f"Mapped {len(module_mapping)} modules by name")
    
    # Build paper name mapping
    cur.execute("SELECT id, name FROM eims_paper")
    old_papers = {row['id']: row['name'] for row in cur.fetchall()}
    
    paper_mapping = {}
    new_papers_by_name = {p.paper_name.strip().lower(): p for p in OccupationPaper.objects.all()}
    for old_id, old_name in old_papers.items():
        if old_name:
            clean_name = old_name.strip().lower()
            if clean_name in new_papers_by_name:
                paper_mapping[old_id] = new_papers_by_name[clean_name]
    log(f"Mapped {len(paper_mapping)} papers by name")
    
    # Get Workers PAS data grouped by (candidate, series, level)
    cur.execute("""
        SELECT 
            cp.candidate_id,
            c.assessment_series_id,
            cp.level_id,
            array_agg(DISTINCT cp.module_id) as module_ids,
            array_agg(DISTINCT cp.paper_id) as paper_ids
        FROM eims_candidatepaper cp
        JOIN eims_candidate c ON cp.candidate_id = c.id
        WHERE c.assessment_series_id IS NOT NULL
        GROUP BY cp.candidate_id, c.assessment_series_id, cp.level_id
        ORDER BY cp.candidate_id, cp.level_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} Workers PAS (candidate, series, level) combinations")
    
    if dry_run:
        # Count unique candidates
        candidates = set(r['candidate_id'] for r in rows)
        log(f"Unique Workers PAS candidates: {len(candidates)}")
        
        # Show sample
        print("\nSample (first 10):")
        for row in rows[:10]:
            level_name = old_levels.get(row['level_id'], 'Unknown')
            print(f"  Candidate {row['candidate_id']}, Series {row['assessment_series_id']}, "
                  f"Level {row['level_id']} ({level_name})")
            print(f"    Modules: {row['module_ids']}, Papers: {row['paper_ids']}")
        return
    
    # Get Workers PAS candidate IDs from old data
    workers_pas_candidates = set(r['candidate_id'] for r in rows)
    
    # Delete existing Workers PAS enrollments that need restructuring
    # Find enrollments for these candidates that have papers (Workers PAS indicator)
    existing_wpas_enrollments = CandidateEnrollment.objects.filter(
        candidate_id__in=workers_pas_candidates,
        papers__isnull=False
    ).distinct()
    
    deleted_count = existing_wpas_enrollments.count()
    log(f"Deleting {deleted_count} existing Workers PAS enrollments for restructure...")
    existing_wpas_enrollments.delete()
    
    # Create new enrollments per (candidate, series, level)
    created_enrollments = 0
    created_modules = 0
    created_papers = 0
    skipped = 0
    
    for row in rows:
        try:
            candidate_id = row['candidate_id']
            series_id = row['assessment_series_id']
            level_id = row['level_id']
            module_ids = row['module_ids']
            paper_ids = row['paper_ids']
            
            # Get candidate
            try:
                candidate = Candidate.objects.get(id=candidate_id)
            except Candidate.DoesNotExist:
                skipped += 1
                continue
            
            # Get series
            try:
                series = AssessmentSeries.objects.get(id=series_id)
            except AssessmentSeries.DoesNotExist:
                skipped += 1
                continue
            
            # Get level
            level = level_mapping.get(level_id)
            if not level:
                skipped += 1
                continue
            
            # Create enrollment for this specific level
            enrollment = CandidateEnrollment.objects.create(
                candidate=candidate,
                assessment_series=series,
                occupation_level=level,
                total_amount=0,
                is_active=True,
            )
            created_enrollments += 1
            
            # Add modules
            for module_id in module_ids:
                if module_id:
                    module = module_mapping.get(module_id)
                    if module:
                        EnrollmentModule.objects.create(
                            enrollment=enrollment,
                            module=module
                        )
                        created_modules += 1
            
            # Add papers
            for paper_id in paper_ids:
                if paper_id:
                    paper = paper_mapping.get(paper_id)
                    if paper:
                        EnrollmentPaper.objects.create(
                            enrollment=enrollment,
                            paper=paper
                        )
                        created_papers += 1
            
            if created_enrollments % 200 == 0:
                log(f"  Progress: {created_enrollments} enrollments...")
                
        except Exception as e:
            log(f"  Error: {e}")
            skipped += 1
    
    log(f"✓ Created {created_enrollments} enrollments, {created_modules} modules, {created_papers} papers")
    log(f"  Skipped: {skipped}")

def run(dry_run=False):
    """Run restructure"""
    log("=" * 50)
    log("RESTRUCTURE: Workers PAS (separate enrollment per level)")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        restructure_workers_pas(dry_run=True)
    else:
        try:
            with transaction.atomic():
                restructure_workers_pas()
                log("=" * 50)
                log("RESTRUCTURE COMPLETED!")
                log("=" * 50)
        except Exception as e:
            log(f"FAILED: {e}")
            raise

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    args = parser.parse_args()
    run(dry_run=args.dry_run)
