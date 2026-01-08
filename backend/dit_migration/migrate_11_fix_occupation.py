#!/usr/bin/env python
"""
Migration script to fix candidates with NULL occupation.
Parses registration number to extract occupation code and maps to correct occupation.

Registration number format: centerno/nationality/entryyear/intake/occCode/gender/number
Example: UVT813/U/25/A/CAU/F/103
         - UVT813 = center number
         - U = nationality
         - 25 = entry year
         - A = intake
         - CAU = occupation code (5th part, after 4 slashes)
         - F = gender
         - 103 = sequential number
"""

import os
import sys

# Add parent directory to path for Django imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emis.settings')
django.setup()

from django.db import transaction
from candidates.models import Candidate
from occupations.models import Occupation


def extract_occ_code_from_regno(regno):
    """
    Extract occupation code from registration number.
    Format: centerno/nationality/entryyear/intake/occCode/gender/number
    """
    if not regno:
        return None
    
    parts = regno.split('/')
    if len(parts) >= 5:
        return parts[4].upper()  # 5th part (index 4) is the occupation code
    return None


def fix_occupation_data(dry_run=True):
    """Fix candidates with NULL occupation by parsing regno"""
    
    # Find all candidates with NULL occupation
    affected_candidates = Candidate.objects.filter(occupation__isnull=True)
    total_affected = affected_candidates.count()
    
    print(f"\n{'='*60}")
    print(f"{'DRY RUN - ' if dry_run else ''}Occupation Fix Migration")
    print(f"{'='*60}")
    print(f"Found {total_affected} candidates with NULL occupation")
    
    if total_affected == 0:
        print("No candidates to fix.")
        return
    
    # Get all occupations for lookup
    occupations = {occ.code.upper(): occ for occ in Occupation.objects.all()}
    print(f"Loaded {len(occupations)} occupations for mapping")
    print(f"Available codes: {sorted(occupations.keys())[:20]}...")
    
    fixed_count = 0
    not_found_codes = {}
    no_code_in_regno = 0
    
    for candidate in affected_candidates:
        occ_code = extract_occ_code_from_regno(candidate.registration_number)
        
        if not occ_code:
            no_code_in_regno += 1
            continue
        
        # Try to find occupation by code
        occupation = occupations.get(occ_code)
        
        if occupation:
            if not dry_run:
                candidate.occupation = occupation
                candidate.save(update_fields=['occupation'])
            fixed_count += 1
            if fixed_count <= 10:  # Show first 10 examples
                print(f"  {candidate.registration_number} -> {occ_code} -> {occupation.name}")
        else:
            # Track codes not found
            if occ_code not in not_found_codes:
                not_found_codes[occ_code] = []
            not_found_codes[occ_code].append(candidate.registration_number)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total candidates with NULL occupation: {total_affected}")
    print(f"{'Would fix' if dry_run else 'Fixed'}: {fixed_count}")
    print(f"Could not extract code from regno: {no_code_in_regno}")
    print(f"Code not found in occupations: {sum(len(v) for v in not_found_codes.values())}")
    
    if not_found_codes:
        print(f"\nCodes not found in occupations table:")
        for code, regnos in sorted(not_found_codes.items()):
            print(f"  {code}: {len(regnos)} candidates")
            if len(regnos) <= 3:
                for regno in regnos:
                    print(f"    - {regno}")
    
    if dry_run:
        print(f"\n*** DRY RUN - No changes made. Run with --apply to fix. ***")


if __name__ == '__main__':
    dry_run = '--apply' not in sys.argv
    
    if dry_run:
        print("\nRunning in DRY RUN mode. Use --apply to actually fix data.")
    else:
        confirm = input("\nThis will UPDATE candidate records. Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
    
    with transaction.atomic():
        fix_occupation_data(dry_run=dry_run)
        
        if dry_run:
            # Rollback in dry run
            transaction.set_rollback(True)
