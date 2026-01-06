#!/usr/bin/env python
"""
Migration Script 8d: Workers PAS Enrollments
Run: python dit_migration/migrate_08d_enrollments_workers_pas.py [--dry-run]

Workers PAS candidates have:
- Assessment Series
- Level
- Module(s)
- Paper(s) under each module

No billing (all assumed paid)
"""
import os
import json
from db_connection import get_old_connection, log, describe_old_table
from django.db import transaction

def show_old_structure():
    """Show structure of old workers PAS enrollment tables"""
    print("\n=== Old Table Structure ===")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Check for workers PAS tables
    tables_to_check = ['eims_candidatepaper', 'eims_paper', 'eims_workerspas']
    
    for table in tables_to_check:
        print(f"\n{table} columns:")
        try:
            cur.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table}'
                ORDER BY ordinal_position
            """)
            cols = cur.fetchall()
            if cols:
                for col in cols:
                    print(f"  {col['column_name']}: {col['data_type']}")
            else:
                print("  (table not found)")
        except Exception as e:
            print(f"  Error: {e}")
    
    cur.close()
    conn.close()

def count_records():
    """Count workers PAS enrollment records"""
    print("\n=== Record Counts ===")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    for table in ['eims_candidatepaper']:
        try:
            cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            result = cur.fetchone()
            print(f"  {table}: {result['cnt'] if result else 0}")
        except:
            print(f"  {table}: (table not found)")
    
    # Count unique candidate-series-level combinations
    try:
        cur.execute("""
            SELECT COUNT(DISTINCT (candidate_id, assessment_series_id, level_id)) as cnt 
            FROM eims_candidatepaper
            WHERE assessment_series_id IS NOT NULL
        """)
        result = cur.fetchone()
        print(f"  Unique enrollments (candidate+series+level): {result['cnt'] if result else 0}")
    except Exception as e:
        print(f"  Error counting unique enrollments: {e}")
    
    cur.close()
    conn.close()

def migrate_workers_pas_enrollments(dry_run=False, skip_existing=True):
    """Migrate workers PAS candidate enrollments"""
    from candidates.models import Candidate, CandidateEnrollment, EnrollmentModule, EnrollmentPaper
    from assessment_series.models import AssessmentSeries
    from occupations.models import OccupationLevel, OccupationModule, OccupationPaper
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Build level name mapping
    old_levels = {}
    for t in ['eims_level', 'eims_occupationlevel']:
        try:
            cur.execute(f"""
                SELECT column_name FROM information_schema.columns WHERE table_name = '{t}'
            """)
            cols = [r['column_name'] for r in cur.fetchall()]
            name_col = 'level_name' if 'level_name' in cols else 'name' if 'name' in cols else None
            if name_col:
                cur.execute(f"SELECT id, {name_col} as level_name FROM {t}")
                old_levels = {row['id']: row['level_name'] for row in cur.fetchall()}
                log(f"Loaded {len(old_levels)} old level names from {t}")
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
    old_modules = {}
    for t in ['eims_module']:
        try:
            cur.execute(f"SELECT id, name FROM {t}")
            old_modules = {row['id']: row['name'] for row in cur.fetchall()}
            log(f"Loaded {len(old_modules)} old module names")
            break
        except:
            pass
    
    module_mapping = {}
    new_modules_by_name = {m.module_name.strip().lower(): m for m in OccupationModule.objects.all()}
    for old_id, old_name in old_modules.items():
        if old_name:
            clean_name = old_name.strip().lower()
            if clean_name in new_modules_by_name:
                module_mapping[old_id] = new_modules_by_name[clean_name]
    log(f"Mapped {len(module_mapping)} modules by name")
    
    # Build paper name mapping
    old_papers = {}
    try:
        cur.execute("SELECT id, name FROM eims_paper")
        old_papers = {row['id']: row['name'] for row in cur.fetchall()}
        log(f"Loaded {len(old_papers)} old paper names")
    except Exception as e:
        log(f"Could not load old papers: {e}")
    
    paper_mapping = {}
    new_papers_by_name = {p.paper_name.strip().lower(): p for p in OccupationPaper.objects.all()}
    for old_id, old_name in old_papers.items():
        if old_name:
            clean_name = old_name.strip().lower()
            if clean_name in new_papers_by_name:
                paper_mapping[old_id] = new_papers_by_name[clean_name]
    log(f"Mapped {len(paper_mapping)} papers by name")
    
    # Get existing enrollments to skip
    existing_pairs = set()
    if skip_existing:
        existing_pairs = set(
            CandidateEnrollment.objects.values_list('candidate_id', 'assessment_series_id')
        )
        log(f"Found {len(existing_pairs)} existing enrollments (will skip)")
    
    # Get workers PAS data grouped by candidate-series-level
    cur.execute("""
        SELECT 
            candidate_id,
            assessment_series_id,
            level_id,
            module_id,
            array_agg(paper_id) as paper_ids
        FROM eims_candidatepaper
        WHERE assessment_series_id IS NOT NULL
        GROUP BY candidate_id, assessment_series_id, level_id, module_id
        ORDER BY candidate_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} workers PAS module-paper combinations")
    
    if dry_run:
        print("\nSample data (first 10):")
        for row in rows[:10]:
            print(f"  Candidate: {row['candidate_id']}, Series: {row['assessment_series_id']}, "
                  f"Level: {row['level_id']}, Module: {row['module_id']}, Papers: {row['paper_ids']}")
        return
    
    # Group by candidate-series to create enrollments
    enrollments_data = {}
    for row in rows:
        key = (row['candidate_id'], row['assessment_series_id'])
        if key not in enrollments_data:
            enrollments_data[key] = {
                'level_id': row['level_id'],
                'modules': {}
            }
        module_id = row['module_id']
        if module_id not in enrollments_data[key]['modules']:
            enrollments_data[key]['modules'][module_id] = []
        enrollments_data[key]['modules'][module_id].extend(row['paper_ids'])
    
    log(f"Grouped into {len(enrollments_data)} unique enrollments")
    
    # Filter out existing
    if skip_existing:
        enrollments_data = {k: v for k, v in enrollments_data.items() if k not in existing_pairs}
        log(f"After filtering existing: {len(enrollments_data)} to migrate")
    
    migrated_enrollments = 0
    migrated_modules = 0
    migrated_papers = 0
    skipped = 0
    
    for (candidate_id, series_id), data in enrollments_data.items():
        try:
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
            level = level_mapping.get(data['level_id'])
            
            # Create enrollment
            enrollment, created = CandidateEnrollment.objects.get_or_create(
                candidate=candidate,
                assessment_series=series,
                defaults={
                    'occupation_level': level,
                    'total_amount': 0,
                    'is_active': True,
                }
            )
            
            if created:
                migrated_enrollments += 1
            
            # Add modules and papers
            for module_id, paper_ids in data['modules'].items():
                module = module_mapping.get(module_id)
                if module:
                    em, _ = EnrollmentModule.objects.get_or_create(
                        enrollment=enrollment,
                        module=module
                    )
                    migrated_modules += 1
                    
                    # Add papers
                    for paper_id in paper_ids:
                        if paper_id:
                            paper = paper_mapping.get(paper_id)
                            if paper:
                                EnrollmentPaper.objects.get_or_create(
                                    enrollment=enrollment,
                                    paper=paper
                                )
                                migrated_papers += 1
            
            if migrated_enrollments % 500 == 0 and migrated_enrollments > 0:
                log(f"  Progress: {migrated_enrollments} enrollments, {migrated_modules} modules, {migrated_papers} papers...")
                
        except Exception as e:
            log(f"  Error: {e}")
            skipped += 1
    
    log(f"✓ Workers PAS: {migrated_enrollments} enrollments, {migrated_modules} modules, {migrated_papers} papers, skipped: {skipped}")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 8d: Workers PAS Enrollments")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_structure()
        count_records()
        migrate_workers_pas_enrollments(dry_run=True)
    else:
        try:
            with transaction.atomic():
                migrate_workers_pas_enrollments()
                log("=" * 50)
                log("MIGRATION 8d COMPLETED!")
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
