#!/usr/bin/env python
"""
Fix Script: Add missing modules and papers to Workers PAS enrollments
Run: python dit_migration/migrate_08d_fix_workers_pas.py [--dry-run]
"""
from db_connection import get_old_connection, log
from django.db import transaction

def fix_workers_pas(dry_run=False):
    """Add missing modules and papers to existing Workers PAS enrollments"""
    from candidates.models import CandidateEnrollment, EnrollmentModule, EnrollmentPaper
    from occupations.models import OccupationModule, OccupationPaper
    
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
    
    # Build paper name mapping
    cur.execute("SELECT id, name FROM eims_paper")
    old_papers = {row['id']: row['name'] for row in cur.fetchall()}
    log(f"Loaded {len(old_papers)} old paper names")
    
    paper_mapping = {}
    new_papers_by_name = {p.paper_name.strip().lower(): p for p in OccupationPaper.objects.all()}
    for old_id, old_name in old_papers.items():
        if old_name:
            clean_name = old_name.strip().lower()
            if clean_name in new_papers_by_name:
                paper_mapping[old_id] = new_papers_by_name[clean_name]
    log(f"Mapped {len(paper_mapping)} papers by name")
    
    # Get all Workers PAS data from old DB (join with candidate for series)
    cur.execute("""
        SELECT cp.candidate_id, c.assessment_series_id, cp.module_id, cp.paper_id
        FROM eims_candidatepaper cp
        JOIN eims_candidate c ON cp.candidate_id = c.id
        WHERE c.assessment_series_id IS NOT NULL
        ORDER BY cp.candidate_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} Workers PAS module-paper selections in old DB")
    
    # Get existing module pairs to skip
    existing_modules = set(
        EnrollmentModule.objects.values_list('enrollment__candidate_id', 'enrollment__assessment_series_id', 'module_id')
    )
    log(f"Found {len(existing_modules)} existing enrollment-module pairs")
    
    # Get existing paper pairs to skip
    existing_papers = set(
        EnrollmentPaper.objects.values_list('enrollment__candidate_id', 'enrollment__assessment_series_id', 'paper_id')
    )
    log(f"Found {len(existing_papers)} existing enrollment-paper pairs")
    
    if dry_run:
        modules_to_add = 0
        papers_to_add = 0
        for row in rows:
            module = module_mapping.get(row['module_id'])
            paper = paper_mapping.get(row['paper_id'])
            if module and (row['candidate_id'], row['assessment_series_id'], module.id) not in existing_modules:
                modules_to_add += 1
            if paper and (row['candidate_id'], row['assessment_series_id'], paper.id) not in existing_papers:
                papers_to_add += 1
        log(f"Would add {modules_to_add} modules, {papers_to_add} papers")
        return
    
    added_modules = 0
    added_papers = 0
    skipped = 0
    
    for row in rows:
        try:
            candidate_id = row['candidate_id']
            series_id = row['assessment_series_id']
            
            # Find enrollment
            try:
                enrollment = CandidateEnrollment.objects.get(
                    candidate_id=candidate_id,
                    assessment_series_id=series_id
                )
            except CandidateEnrollment.DoesNotExist:
                skipped += 1
                continue
            
            # Add module if not exists
            module = module_mapping.get(row['module_id'])
            if module and (candidate_id, series_id, module.id) not in existing_modules:
                EnrollmentModule.objects.get_or_create(
                    enrollment=enrollment,
                    module=module
                )
                existing_modules.add((candidate_id, series_id, module.id))
                added_modules += 1
            
            # Add paper if not exists
            paper = paper_mapping.get(row['paper_id'])
            if paper and (candidate_id, series_id, paper.id) not in existing_papers:
                EnrollmentPaper.objects.get_or_create(
                    enrollment=enrollment,
                    paper=paper
                )
                existing_papers.add((candidate_id, series_id, paper.id))
                added_papers += 1
                
        except Exception as e:
            log(f"  Error: {e}")
            skipped += 1
    
    log(f"✓ Added {added_modules} modules, {added_papers} papers, skipped: {skipped}")

def run(dry_run=False):
    """Run fix"""
    log("=" * 50)
    log("FIX: Workers PAS modules and papers")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        fix_workers_pas(dry_run=True)
    else:
        fix_workers_pas()
        log("=" * 50)
        log("FIX COMPLETED!")
        log("=" * 50)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview without making changes')
    args = parser.parse_args()
    run(dry_run=args.dry_run)
