#!/usr/bin/env python
"""
Migration Script 8b: Modular Enrollments
Run: python dit_migration/migrate_08b_enrollments_modular.py [--dry-run]

Migrates:
1. CandidateEnrollment - links candidate to assessment series and level
2. EnrollmentModule - modules selected for the enrollment

Only for MODULAR candidates (category = 3 or 'modular')
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
    
    # Check for enrollment tables
    tables_to_check = [
        'eims_candidateenrollment', 
        'eims_enrollment',
        'eims_candidatemodule',
        'eims_enrollmentmodule',
        'eims_moduleenrollment'
    ]
    
    conn = get_old_connection()
    cur = conn.cursor()
    
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
    """Count modular enrollment records"""
    print("\n=== Record Counts ===")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Count modular candidates
    try:
        cur.execute("""
            SELECT COUNT(*) as cnt FROM eims_candidate 
            WHERE category = 3 OR category = '3' OR registration_category = 'modular'
        """)
        result = cur.fetchone()
        print(f"  Modular candidates: {result['cnt'] if result else 0}")
    except Exception as e:
        print(f"  Error counting modular candidates: {e}")
    
    # Try to find enrollment table
    for table in ['eims_candidateenrollment', 'eims_enrollment']:
        try:
            cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            result = cur.fetchone()
            print(f"  {table}: {result['cnt'] if result else 0}")
        except:
            pass
    
    cur.close()
    conn.close()

def migrate_modular_enrollments(dry_run=False, skip_existing=True):
    """Migrate modular candidate enrollments"""
    from candidates.models import Candidate, CandidateEnrollment, EnrollmentModule
    from assessment_series.models import AssessmentSeries
    from occupations.models import OccupationLevel, OccupationModule
    
    level_mapping = load_level_mapping()
    
    # Get existing enrollment IDs to skip
    existing_ids = set()
    if skip_existing:
        existing_ids = set(CandidateEnrollment.objects.values_list('id', flat=True))
        log(f"Found {len(existing_ids)} existing enrollments (will skip)")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # First, find the correct enrollment table structure
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE '%enrollment%' OR table_name LIKE '%enrolment%')
    """)
    enrollment_tables = [r['table_name'] for r in cur.fetchall()]
    log(f"Found enrollment tables: {enrollment_tables}")
    
    if not enrollment_tables:
        log("No enrollment tables found!")
        cur.close()
        conn.close()
        return
    
    # Try to get enrollments - adjust query based on actual table structure
    enrollment_table = enrollment_tables[0]
    
    # Get columns to understand structure
    cur.execute(f"""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = '{enrollment_table}'
    """)
    columns = [r['column_name'] for r in cur.fetchall()]
    log(f"Enrollment table columns: {columns}")
    
    # Build query based on available columns
    candidate_col = 'candidate_id' if 'candidate_id' in columns else 'id'
    series_col = 'assessment_series_id' if 'assessment_series_id' in columns else 'series_id'
    level_col = 'level_id' if 'level_id' in columns else 'occupation_level_id'
    
    # Get modular enrollments
    query = f"""
        SELECT e.*, c.category, c.registration_category
        FROM {enrollment_table} e
        JOIN eims_candidate c ON e.{candidate_col} = c.id
        WHERE c.category = 3 OR c.category = '3' OR c.registration_category = 'modular'
        ORDER BY e.id
    """
    
    try:
        cur.execute(query)
        rows = cur.fetchall()
    except Exception as e:
        log(f"Error querying enrollments: {e}")
        log("Trying alternative approach...")
        
        # Alternative: get modular candidates and their series
        cur.execute("""
            SELECT c.id as candidate_id, c.series_id, c.level_id
            FROM eims_candidate c
            WHERE (c.category = 3 OR c.category = '3' OR c.registration_category = 'modular')
            AND c.series_id IS NOT NULL
            ORDER BY c.id
        """)
        rows = cur.fetchall()
    
    log(f"Found {len(rows)} modular enrollments")
    
    if dry_run:
        print("\nSample enrollments (first 10):")
        for row in rows[:10]:
            print(f"  ID: {row.get('id')}, Candidate: {row.get('candidate_id')}, "
                  f"Series: {row.get('series_id') or row.get('assessment_series_id')}, "
                  f"Level: {row.get('level_id') or row.get('occupation_level_id')}")
        cur.close()
        conn.close()
        return
    
    # Filter out existing
    if skip_existing and 'id' in rows[0] if rows else False:
        rows = [r for r in rows if r.get('id') not in existing_ids]
        log(f"After filtering existing: {len(rows)} to migrate")
    
    migrated = 0
    skipped = 0
    
    for row in rows:
        try:
            # Get candidate
            candidate_id = row.get('candidate_id')
            try:
                candidate = Candidate.objects.get(id=candidate_id)
            except Candidate.DoesNotExist:
                skipped += 1
                continue
            
            # Get series
            series_id = row.get('series_id') or row.get('assessment_series_id')
            series = None
            if series_id:
                try:
                    series = AssessmentSeries.objects.get(id=series_id)
                except AssessmentSeries.DoesNotExist:
                    pass
            
            if not series:
                skipped += 1
                continue
            
            # Get level with mapping
            old_level_id = row.get('level_id') or row.get('occupation_level_id')
            level = None
            if old_level_id:
                new_level_id = level_mapping.get(str(old_level_id), old_level_id)
                try:
                    level = OccupationLevel.objects.get(id=new_level_id)
                except OccupationLevel.DoesNotExist:
                    try:
                        level = OccupationLevel.objects.get(id=old_level_id)
                    except OccupationLevel.DoesNotExist:
                        pass
            
            # Create enrollment - no billing (total_amount = 0)
            enrollment_id = row.get('id')
            if enrollment_id:
                enrollment, created = CandidateEnrollment.objects.update_or_create(
                    id=enrollment_id,
                    defaults={
                        'candidate': candidate,
                        'assessment_series': series,
                        'occupation_level': level,
                        'total_amount': 0,  # No billing
                        'is_active': True,
                    }
                )
            else:
                enrollment, created = CandidateEnrollment.objects.get_or_create(
                    candidate=candidate,
                    assessment_series=series,
                    defaults={
                        'occupation_level': level,
                        'total_amount': 0,
                        'is_active': True,
                    }
                )
            
            migrated += 1
            
            if migrated % 1000 == 0:
                log(f"  Progress: {migrated} enrollments migrated...")
                
        except Exception as e:
            log(f"  Error migrating enrollment {row.get('id')}: {e}")
            skipped += 1
    
    cur.close()
    conn.close()
    log(f"✓ Modular enrollments migrated: {migrated}, skipped: {skipped}")

def migrate_enrollment_modules(dry_run=False, skip_existing=True):
    """Migrate modules selected for modular enrollments"""
    from candidates.models import CandidateEnrollment, EnrollmentModule
    from occupations.models import OccupationModule
    
    # Get existing enrollment-module pairs to skip
    existing_pairs = set()
    if skip_existing:
        existing_pairs = set(
            EnrollmentModule.objects.values_list('enrollment_id', 'module_id')
        )
        log(f"Found {len(existing_pairs)} existing enrollment-module pairs (will skip)")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Find module enrollment table
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE '%candidatemodule%' OR table_name LIKE '%enrollmentmodule%' 
             OR table_name LIKE '%moduleenrollment%')
    """)
    module_tables = [r['table_name'] for r in cur.fetchall()]
    
    if not module_tables:
        log("No module enrollment tables found - checking for modules in candidate table")
        # Some systems store modules directly in enrollment or as separate records
        cur.close()
        conn.close()
        return
    
    module_table = module_tables[0]
    log(f"Using module table: {module_table}")
    
    # Get columns
    cur.execute(f"""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = '{module_table}'
    """)
    columns = [r['column_name'] for r in cur.fetchall()]
    log(f"Module table columns: {columns}")
    
    # Build query
    enrollment_col = 'enrollment_id' if 'enrollment_id' in columns else 'candidate_enrollment_id'
    module_col = 'module_id' if 'module_id' in columns else 'occupation_module_id'
    
    cur.execute(f"SELECT * FROM {module_table} ORDER BY id")
    rows = cur.fetchall()
    
    log(f"Found {len(rows)} module selections")
    
    if dry_run:
        print("\nSample module selections (first 10):")
        for row in rows[:10]:
            print(f"  Enrollment: {row.get(enrollment_col)}, Module: {row.get(module_col)}")
        cur.close()
        conn.close()
        return
    
    migrated = 0
    skipped = 0
    
    for row in rows:
        try:
            enrollment_id = row.get(enrollment_col) or row.get('enrollment_id')
            module_id = row.get(module_col) or row.get('module_id')
            
            if not enrollment_id or not module_id:
                skipped += 1
                continue
            
            # Skip if already exists
            if (enrollment_id, module_id) in existing_pairs:
                skipped += 1
                continue
            
            # Get enrollment
            try:
                enrollment = CandidateEnrollment.objects.get(id=enrollment_id)
            except CandidateEnrollment.DoesNotExist:
                skipped += 1
                continue
            
            # Get module
            try:
                module = OccupationModule.objects.get(id=module_id)
            except OccupationModule.DoesNotExist:
                skipped += 1
                continue
            
            EnrollmentModule.objects.get_or_create(
                enrollment=enrollment,
                module=module
            )
            migrated += 1
            
        except Exception as e:
            log(f"  Error: {e}")
            skipped += 1
    
    cur.close()
    conn.close()
    log(f"✓ Enrollment modules migrated: {migrated}, skipped: {skipped}")

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
        migrate_enrollment_modules(dry_run=True)
    else:
        try:
            with transaction.atomic():
                migrate_modular_enrollments()
                migrate_enrollment_modules()
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
