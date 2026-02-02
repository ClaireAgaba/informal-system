#!/usr/bin/env python
"""
Migration Script 10: Fix Candidate Disability Data
Run: python dit_migration/migrate_10_fix_disability.py [--dry-run]

Updates candidates with disability info from old system:
- has_disability = True
- nature_of_disability (FK)
- disability_specification (text)
"""
import os
import sys

# Add parent directory to path for Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emis.settings')
import django
django.setup()

from db_connection import get_old_connection, log, describe_old_table
from django.db import transaction


def show_old_structure():
    """Show structure of old table disability fields"""
    print("\n=== Old Candidate Disability Fields ===")
    try:
        for col in describe_old_table('eims_candidate'):
            if 'disab' in col['column_name'].lower():
                print(f"  {col['column_name']}: {col['data_type']}")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n=== Old Nature of Disability Table ===")
    try:
        for col in describe_old_table('eims_natureofdisability'):
            print(f"  {col['column_name']}: {col['data_type']}")
    except Exception as e:
        print(f"  Error: {e}")


def count_disabled_candidates():
    """Count candidates with disability in old system"""
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Check all disability-related column names
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'eims_candidate' AND (column_name LIKE '%disab%' OR column_name LIKE '%nature%')
    """)
    cols = cur.fetchall()
    print("\n=== Disability columns in old DB ===")
    for col in cols:
        print(f"  {col['column_name']}")
    
    # Count disabled candidates - column is "disability"
    cur.execute("SELECT COUNT(*) as cnt FROM eims_candidate WHERE disability = true")
    result = cur.fetchone()
    disabled_count = result['cnt'] if result else 0
    
    cur.close()
    conn.close()
    
    print(f"\n=== Disabled Candidates in Old System ===")
    print(f"Total: {disabled_count}")
    
    return disabled_count


def migrate_nature_of_disability(dry_run=False):
    """Migrate nature of disability types"""
    from configurations.models import NatureOfDisability
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_natureofdisability ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} nature of disability types in old system")
    
    if dry_run:
        print("\nNature of Disability types:")
        for row in rows:
            print(f"  ID: {row['id']}, Name: {row['name']}")
        return {}
    
    # Create mapping of old ID to new object
    mapping = {}
    created = 0
    existing = 0
    
    for row in rows:
        nod, was_created = NatureOfDisability.objects.get_or_create(
            name=row['name'],
            defaults={'description': row.get('description', '')}
        )
        mapping[row['id']] = nod
        if was_created:
            created += 1
        else:
            existing += 1
    
    log(f"Nature of Disability: {created} created, {existing} already existed")
    return mapping


def fix_disability_data(dry_run=False):
    """Update candidates with disability data"""
    from candidates.models import Candidate
    from configurations.models import NatureOfDisability
    
    # First migrate nature of disability types
    nod_mapping = migrate_nature_of_disability(dry_run)
    
    conn = get_old_connection()
    cur = conn.cursor()
    
    # Get all candidates with disability from old system
    # Try to capture nature of disability too (if present in old schema)
    cur.execute("""
        SELECT
            c.id,
            c.disability,
            c.disability_specification,
            c.nature_of_disability_id AS nature_of_disability_id,
            nod.name AS nature_of_disability_name
        FROM eims_candidate c
        LEFT JOIN eims_natureofdisability nod ON nod.id = c.nature_of_disability_id
        WHERE c.disability = true
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    log(f"Found {len(rows)} candidates with disability to update")
    
    if dry_run:
        print("\nSample disabled candidates (first 10):")
        for row in rows[:10]:
            print(f"  ID: {row['id']}, Spec: {(row['disability_specification'] or '')[:50]}...")
        return
    
    updated = 0
    not_found = 0
    already_complete = 0
    
    # Build NatureOfDisability lookup by name for fallback
    nod_by_name = {nod.name.lower(): nod for nod in NatureOfDisability.objects.all()}
    
    with transaction.atomic():
        for row in rows:
            try:
                candidate = Candidate.objects.get(id=row['id'])
                
                # If already fully populated, skip
                if candidate.has_disability and candidate.nature_of_disability:
                    already_complete += 1
                    continue

                update_fields = []

                # Ensure has_disability
                if not candidate.has_disability:
                    candidate.has_disability = True
                    update_fields.append('has_disability')

                # Set disability specification if missing/empty
                old_spec = (row.get('disability_specification') or '').strip()
                if old_spec and not (candidate.disability_specification or '').strip():
                    candidate.disability_specification = old_spec
                    update_fields.append('disability_specification')

                # Set nature_of_disability if missing
                if not candidate.nature_of_disability:
                    old_nod_id = row.get('nature_of_disability_id')
                    old_nod_name = (row.get('nature_of_disability_name') or '').strip()
                    nod_obj = None

                    if old_nod_id and old_nod_id in nod_mapping:
                        nod_obj = nod_mapping[old_nod_id]
                    elif old_nod_name:
                        nod_obj = nod_by_name.get(old_nod_name.lower())
                        if not nod_obj:
                            nod_obj, _ = NatureOfDisability.objects.get_or_create(name=old_nod_name)
                            nod_by_name[old_nod_name.lower()] = nod_obj

                    if nod_obj:
                        candidate.nature_of_disability = nod_obj
                        update_fields.append('nature_of_disability')

                if update_fields:
                    candidate.save(update_fields=update_fields)
                    updated += 1
                
            except Candidate.DoesNotExist:
                not_found += 1
    
    log(f"Updated: {updated}, Already complete: {already_complete}, Not found in new system: {not_found}")


if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    structure = '--structure' in sys.argv
    
    if structure:
        show_old_structure()
        count_disabled_candidates()
    elif dry_run:
        print("=== DRY RUN MODE ===")
        count_disabled_candidates()
        fix_disability_data(dry_run=True)
    else:
        print("=== LIVE MIGRATION ===")
        fix_disability_data(dry_run=False)
        print("\nDone!")
