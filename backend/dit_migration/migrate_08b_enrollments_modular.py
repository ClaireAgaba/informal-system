#!/usr/bin/env python
"""
Migration Script 8b: Modular Enrollments
Run: python dit_migration/migrate_08b_enrollments_modular.py [--dry-run]

Old DB structure: eims_candidatemodule table contains:
- candidate_id, module_id, assessment_series_id, marks, status

This script:
1. Groups by (candidate_id, assessment_series_id) to create CandidateEnrollment
2. Creates EnrollmentModule for each module selection

No billing applied - all assumed paid.
"""
import os
import json
from db_connection import get_old_connection, log, get_old_table_count, describe_old_table
from django.db import transaction

# Load mappings
LEVEL_MAPPING_FILE = os.path.join(os.path.dirname(__file__), 'level_mapping.json')

def load_level_mapping():
    """Load level ID mapping (old_level_id -> new_level_id)"""
    if os.path.exists(LEVEL_MAPPING_FILE):
        with open(LEVEL_MAPPING_FILE, 'r') as f:
            return json.load(f)
    return {}

def show_old_structure():
    """Show structure of old enrollment tables"""
    print("\n=== Old Table Structure ===")
    print("\neims_candidatemodule columns:")
    for col in describe_old_table('eims_candidatemodule'):
        print(f"  {col['column_name']}: {col['data_type']}")

def count_records():
    """Count modular enrollment records"""
    print("\n=== Record Counts ===")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Count total records
    cur.execute("SELECT COUNT(*) as cnt FROM eims_candidatemodule")
    result = cur.fetchone()
    print(f"  eims_candidatemodule total: {result['cnt'] if result else 0}")
    
    # Count unique enrollments (candidate + series combinations)
    cur.execute("""
        SELECT COUNT(DISTINCT (candidate_id, assessment_series_id)) as cnt 
        FROM eims_candidatemodule
    """)
    result = cur.fetchone()
    print(f"  Unique enrollments (candidate+series): {result['cnt'] if result else 0}")
    
    cur.close()
    conn.close()

def migrate_modular_enrollments(dry_run=False, skip_existing=True):
    """Migrate modular candidate enrollments from eims_candidatemodule"""
    from candidates.models import Candidate, CandidateEnrollment, EnrollmentModule
    from assessment_series.models import AssessmentSeries
    from occupations.models import OccupationLevel, OccupationModule
    
    level_mapping = load_level_mapping()
    
    # Get existing (candidate_id, series_id) pairs to skip
    existing_pairs = set()
    if skip_existing:
        existing_pairs = set(
            CandidateEnrollment.objects.values_list('candidate_id', 'assessment_series_id')
        )
        log(f"Found {len(existing_pairs)} existing enrollments (will skip)")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Get unique enrollment combinations with their modules
    cur.execute("""
        SELECT 
            candidate_id,
            assessment_series_id,
            array_agg(module_id) as module_ids,
            MIN(enrolled_at) as enrolled_at
        FROM eims_candidatemodule
        WHERE assessment_series_id IS NOT NULL
        GROUP BY candidate_id, assessment_series_id
        ORDER BY candidate_id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} unique enrollments (candidate + series)")
    
    if dry_run:
        print("\nSample enrollments (first 10):")
        for row in rows[:10]:
            print(f"  Candidate: {row['candidate_id']}, Series: {row['assessment_series_id']}, "
                  f"Modules: {row['module_ids']}")
        return
    
    # Filter out existing
    if skip_existing:
        rows = [r for r in rows if (r['candidate_id'], r['assessment_series_id']) not in existing_pairs]
        log(f"After filtering existing: {len(rows)} to migrate")
    
    migrated_enrollments = 0
    migrated_modules = 0
    skipped = 0
    
    for row in rows:
        try:
            candidate_id = row['candidate_id']
            series_id = row['assessment_series_id']
            module_ids = row['module_ids']
            
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
            
            # Get level from candidate's occupation (for modular, level comes from module)
            level = None
            if candidate.occupation:
                # Try to get first level for this occupation
                level = OccupationLevel.objects.filter(occupation=candidate.occupation).first()
            
            # Create enrollment - no billing
            enrollment, created = CandidateEnrollment.objects.get_or_create(
                candidate=candidate,
                assessment_series=series,
                defaults={
                    'occupation_level': level,
                    'total_amount': 0,  # No billing
                    'is_active': True,
                }
            )
            
            if created:
                migrated_enrollments += 1
            
            # Create EnrollmentModule for each module
            for module_id in module_ids:
                if module_id:
                    try:
                        module = OccupationModule.objects.get(id=module_id)
                        EnrollmentModule.objects.get_or_create(
                            enrollment=enrollment,
                            module=module
                        )
                        migrated_modules += 1
                    except OccupationModule.DoesNotExist:
                        pass
            
            if migrated_enrollments % 1000 == 0 and migrated_enrollments > 0:
                log(f"  Progress: {migrated_enrollments} enrollments, {migrated_modules} modules...")
                
        except Exception as e:
            log(f"  Error: {e}")
            skipped += 1
    
    log(f"✓ Enrollments migrated: {migrated_enrollments}, modules: {migrated_modules}, skipped: {skipped}")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 8b: Modular Enrollments")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_structure()
        count_records()
        migrate_modular_enrollments(dry_run=True)
    else:
        try:
            with transaction.atomic():
                migrate_modular_enrollments()
                log("=" * 50)
                log("MIGRATION 8b COMPLETED!")
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
