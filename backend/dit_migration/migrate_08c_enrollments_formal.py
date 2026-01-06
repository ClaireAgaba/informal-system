#!/usr/bin/env python
"""
Migration Script 8c: Formal Enrollments
Run: python dit_migration/migrate_08c_enrollments_formal.py [--dry-run]

For formal candidates:
- Links candidate to assessment series
- Links to occupation level
- No billing (all assumed paid)

Formal candidates have assessment series and level stored in a separate table
or in the candidate record itself.
"""
import os
import json
from db_connection import get_old_connection, log, describe_old_table
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
    """Show structure of old formal enrollment tables"""
    print("\n=== Old Table Structure ===")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Check for formal enrollment tables
    tables_to_check = ['eims_candidatelevel', 'eims_formalenrollment', 'eims_levelenrollment']
    
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
    
    # Also check eims_candidate for series/level fields
    print("\neims_candidate series/level columns:")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'eims_candidate'
        AND (column_name LIKE '%series%' OR column_name LIKE '%level%')
        ORDER BY ordinal_position
    """)
    for col in cur.fetchall():
        print(f"  {col['column_name']}: {col['data_type']}")
    
    cur.close()
    conn.close()

def count_records():
    """Count formal enrollment records"""
    print("\n=== Record Counts ===")
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Check for candidatelevel table
    try:
        cur.execute("SELECT COUNT(*) as cnt FROM eims_candidatelevel")
        result = cur.fetchone()
        print(f"  eims_candidatelevel: {result['cnt'] if result else 0}")
    except:
        print("  eims_candidatelevel: (table not found)")
    
    cur.close()
    conn.close()

def migrate_formal_enrollments(dry_run=False, skip_existing=True):
    """Migrate formal candidate enrollments"""
    from candidates.models import Candidate, CandidateEnrollment
    from assessment_series.models import AssessmentSeries
    from occupations.models import OccupationLevel
    
    # Build level name mapping (old level_id -> new level by name)
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Find level table
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%level%'
    """)
    level_tables = [r['table_name'] for r in cur.fetchall()]
    log(f"Found level tables: {level_tables}")
    
    # Get old level names
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
    
    # Build level mapping by name
    level_mapping = {}
    new_levels_by_name = {l.level_name.strip().lower(): l for l in OccupationLevel.objects.all()}
    for old_id, old_name in old_levels.items():
        if old_name:
            clean_name = old_name.strip().lower()
            if clean_name in new_levels_by_name:
                level_mapping[old_id] = new_levels_by_name[clean_name]
    log(f"Mapped {len(level_mapping)} levels by name")
    
    # Get existing (candidate_id, series_id) pairs to skip
    existing_pairs = set()
    if skip_existing:
        existing_pairs = set(
            CandidateEnrollment.objects.values_list('candidate_id', 'assessment_series_id')
        )
        log(f"Found {len(existing_pairs)} existing enrollments (will skip)")
    
    # Try to find formal enrollments table
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE '%candidatelevel%' OR table_name LIKE '%formalenroll%')
    """)
    enrollment_tables = [r['table_name'] for r in cur.fetchall()]
    
    if 'eims_candidatelevel' in enrollment_tables:
        # Get columns
        cur.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'eims_candidatelevel'
        """)
        cols = [r['column_name'] for r in cur.fetchall()]
        log(f"eims_candidatelevel columns: {cols}")
        
        # Get formal enrollments
        cur.execute("""
            SELECT * FROM eims_candidatelevel
            WHERE assessment_series_id IS NOT NULL
            ORDER BY candidate_id
        """)
        rows = cur.fetchall()
    else:
        log("No formal enrollment table found, trying candidate table directly")
        # Some systems store level enrollment in candidate record
        cur.execute("""
            SELECT id as candidate_id, series_id as assessment_series_id, level_id
            FROM eims_candidate
            WHERE series_id IS NOT NULL AND level_id IS NOT NULL
            ORDER BY id
        """)
        rows = cur.fetchall()
    
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} formal enrollments")
    
    if dry_run:
        print("\nSample enrollments (first 10):")
        for row in rows[:10]:
            print(f"  Candidate: {row.get('candidate_id')}, Series: {row.get('assessment_series_id')}, "
                  f"Level: {row.get('level_id')}")
        return
    
    # Filter out existing
    if skip_existing:
        rows = [r for r in rows if (r['candidate_id'], r['assessment_series_id']) not in existing_pairs]
        log(f"After filtering existing: {len(rows)} to migrate")
    
    migrated = 0
    skipped = 0
    
    for row in rows:
        try:
            candidate_id = row['candidate_id']
            series_id = row['assessment_series_id']
            level_id = row.get('level_id')
            
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
            
            # Get level (by name mapping)
            level = level_mapping.get(level_id)
            if not level and level_id:
                # Try direct lookup
                try:
                    level = OccupationLevel.objects.get(id=level_id)
                except OccupationLevel.DoesNotExist:
                    pass
            
            # Create enrollment - no billing
            CandidateEnrollment.objects.get_or_create(
                candidate=candidate,
                assessment_series=series,
                defaults={
                    'occupation_level': level,
                    'total_amount': 0,  # No billing
                    'is_active': True,
                }
            )
            migrated += 1
            
            if migrated % 1000 == 0:
                log(f"  Progress: {migrated} enrollments migrated...")
                
        except Exception as e:
            log(f"  Error: {e}")
            skipped += 1
    
    log(f"✓ Formal enrollments migrated: {migrated}, skipped: {skipped}")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 8c: Formal Enrollments")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_structure()
        count_records()
        migrate_formal_enrollments(dry_run=True)
    else:
        try:
            with transaction.atomic():
                migrate_formal_enrollments()
                log("=" * 50)
                log("MIGRATION 8c COMPLETED!")
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
