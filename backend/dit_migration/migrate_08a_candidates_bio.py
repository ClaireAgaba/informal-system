#!/usr/bin/env python
"""
Migration Script 8a: Candidates Bio Data
Run: python dit_migration/migrate_08a_candidates_bio.py [--dry-run]

This migrates all candidates bio data WITHOUT enrollments or results.
No billing is applied - all assumed paid from old system.
"""
import os
import json
from db_connection import get_old_connection, log, get_old_table_count, describe_old_table
from django.db import transaction

# Load occupation mapping
MAPPING_FILE = os.path.join(os.path.dirname(__file__), 'occupation_mapping.json')

def load_occupation_mapping():
    """Load occupation ID mapping (old_occ_id -> new_occ_id)"""
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r') as f:
            return json.load(f)
    return {}

def show_old_structure():
    """Show structure of old tables"""
    print("\n=== Old Table Structure ===")
    print("\neims_candidate columns:")
    try:
        for col in describe_old_table('eims_candidate'):
            print(f"  {col['column_name']}: {col['data_type']}")
    except Exception as e:
        print(f"  Error: {e}")

def count_records():
    """Count records in old tables"""
    print("\n=== Record Counts ===")
    try:
        print(f"  eims_candidate: {get_old_table_count('eims_candidate')}")
    except:
        print("  eims_candidate: Table not found")

def migrate_candidates(dry_run=False, skip_existing=True):
    """Migrate candidates bio data"""
    from candidates.models import Candidate
    from configurations.models import District, Village, NatureOfDisability
    from assessment_centers.models import AssessmentCenter, CenterBranch
    from occupations.models import Occupation
    
    occ_mapping = load_occupation_mapping()
    
    # Get existing candidate IDs to skip
    existing_ids = set()
    if skip_existing:
        existing_ids = set(Candidate.objects.values_list('id', flat=True))
        log(f"Found {len(existing_ids)} existing candidates in new database (will skip)")
    
    conn = get_old_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM eims_candidate ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Filter out existing candidates
    if skip_existing:
        rows = [r for r in rows if r['id'] not in existing_ids]
    
    log(f"Found {len(rows)} candidates to migrate")
    
    if dry_run:
        print("\nSample data (first 10):")
        for row in rows[:10]:
            print(f"  ID: {row['id']}, Name: {row.get('name') or row.get('full_name')}, "
                  f"Reg#: {row.get('reg_number') or row.get('registration_number')}, "
                  f"Center: {row.get('center_id') or row.get('assessment_center_id')}, "
                  f"Category: {row.get('category') or row.get('registration_category')}")
        
        # Show category distribution
        print("\n=== Category Distribution ===")
        categories = {}
        for row in rows:
            cat = row.get('category') or row.get('registration_category') or 'unknown'
            categories[cat] = categories.get(cat, 0) + 1
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count}")
        return
    
    migrated = 0
    skipped = 0
    errors = []
    
    for row in rows:
        try:
            # Get basic info
            full_name = (row.get('name') or row.get('full_name') or '')[:200]
            if not full_name:
                skipped += 1
                continue
            
            # Get registration number
            reg_number = row.get('reg_number') or row.get('registration_number') or ''
            
            # Get center
            center_id = row.get('center_id') or row.get('assessment_center_id')
            center = None
            if center_id:
                try:
                    center = AssessmentCenter.objects.get(id=center_id)
                except AssessmentCenter.DoesNotExist:
                    pass
            
            # Get branch
            branch = None
            branch_id = row.get('branch_id') or row.get('assessment_center_branch_id')
            if branch_id:
                try:
                    branch = CenterBranch.objects.get(id=branch_id)
                except CenterBranch.DoesNotExist:
                    pass
            
            # Get district and village
            district = None
            district_id = row.get('district_id')
            if district_id:
                try:
                    district = District.objects.get(id=district_id)
                except District.DoesNotExist:
                    pass
            
            village = None
            village_id = row.get('village_id')
            if village_id:
                try:
                    village = Village.objects.get(id=village_id)
                except Village.DoesNotExist:
                    pass
            
            # Get occupation with mapping
            occupation = None
            occ_id = row.get('occupation_id')
            if occ_id:
                # Check if we need to map to a non-old occupation
                mapped_occ_id = occ_mapping.get(str(occ_id), occ_id)
                try:
                    occupation = Occupation.objects.get(id=mapped_occ_id)
                except Occupation.DoesNotExist:
                    # Try original ID
                    try:
                        occupation = Occupation.objects.get(id=occ_id)
                    except Occupation.DoesNotExist:
                        pass
            
            # Map category (old: 1=formal, 2=workers_pas, 3=modular or text values)
            old_category = row.get('category') or row.get('registration_category')
            if old_category in [1, '1', 'formal']:
                registration_category = 'formal'
            elif old_category in [2, '2', 'workers_pas', 'workers pas']:
                registration_category = 'workers_pas'
            elif old_category in [3, '3', 'modular']:
                registration_category = 'modular'
            else:
                registration_category = 'formal'  # default
            
            # Map gender
            old_gender = row.get('gender') or row.get('sex') or ''
            if old_gender.lower() in ['m', 'male']:
                gender = 'male'
            elif old_gender.lower() in ['f', 'female']:
                gender = 'female'
            else:
                gender = 'other'
            
            # Get dates
            dob = row.get('date_of_birth') or row.get('dob')
            entry_year = row.get('entry_year') or row.get('year') or 2024
            intake = row.get('intake') or 'M'
            if intake not in ['M', 'A']:
                intake = 'M'
            
            # Contact
            contact = (row.get('contact') or row.get('phone') or row.get('telephone') or '')[:20]
            
            # Nationality
            nationality = row.get('nationality') or 'Uganda'
            
            # Refugee info
            is_refugee = row.get('is_refugee', False) or False
            refugee_number = row.get('refugee_number') or ''
            
            # Disability info
            has_disability = row.get('has_disability', False) or row.get('is_disabled', False) or False
            disability_id = row.get('nature_of_disability_id') or row.get('disability_id')
            nature_of_disability = None
            if disability_id:
                try:
                    nature_of_disability = NatureOfDisability.objects.get(id=disability_id)
                except NatureOfDisability.DoesNotExist:
                    pass
            
            # Status
            old_status = row.get('status') or 'active'
            if old_status in ['active', 'inactive', 'suspended', 'completed']:
                status = old_status
            else:
                status = 'active'
            
            # Create or update candidate
            Candidate.objects.update_or_create(
                id=row['id'],
                defaults={
                    'full_name': full_name,
                    'registration_number': reg_number[:50] if reg_number else None,
                    'reg_number': reg_number[:100] if reg_number else '',
                    'date_of_birth': dob,
                    'gender': gender,
                    'nationality': nationality,
                    'contact': contact or '0700000000',
                    'district': district,
                    'village': village,
                    'assessment_center': center,
                    'assessment_center_branch': branch,
                    'occupation': occupation,
                    'registration_category': registration_category,
                    'entry_year': entry_year,
                    'intake': intake,
                    'is_refugee': is_refugee,
                    'refugee_number': refugee_number[:100] if refugee_number else '',
                    'has_disability': has_disability,
                    'nature_of_disability': nature_of_disability,
                    'status': status,
                    'is_submitted': True,  # All migrated candidates are submitted
                    'verification_status': 'verified',  # All migrated candidates are verified
                    'payment_cleared': True,  # No billing for migrated candidates
                    'fees_balance': 0,  # All assumed paid
                }
            )
            migrated += 1
            
            if migrated % 1000 == 0:
                log(f"  Progress: {migrated} candidates migrated...")
            
        except Exception as e:
            errors.append(f"Candidate {row['id']}: {e}")
            skipped += 1
            if len(errors) <= 10:
                log(f"  Error migrating candidate {row['id']}: {e}")
    
    log(f"✓ Candidates migrated: {migrated}, skipped: {skipped}")
    if len(errors) > 10:
        log(f"  ... and {len(errors) - 10} more errors")

def run(dry_run=False):
    """Run migration"""
    log("=" * 50)
    log("MIGRATION 8a: Candidates Bio Data")
    log("=" * 50)
    
    if dry_run:
        log("DRY RUN MODE - No changes will be made")
        show_old_structure()
        count_records()
        migrate_candidates(dry_run=True)
    else:
        try:
            with transaction.atomic():
                migrate_candidates()
                log("=" * 50)
                log("MIGRATION 8a COMPLETED!")
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
