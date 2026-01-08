#!/usr/bin/env python
"""
Map missing occupation codes to existing occupations and update registration numbers.
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

# Mapping of missing codes to existing occupation codes
CODE_MAPPINGS = {
    'MFR': 'MF',  # Mushroom Farmer
    'WR': 'WE',   # Weaver
    'VGF': 'VF',  # Vegetable Farmer
    'BFM': 'BF',  # Banana Farmer
    'DAR': 'DA',  # Drama Artist
    'GD': 'TL',   # Tailor
}

def map_missing_occupations(dry_run=True):
    """Map missing occupation codes to existing ones (no registration number changes)"""
    
    print(f"\n{'='*60}")
    print(f"{'DRY RUN - ' if dry_run else ''}Map Missing Occupations")
    print(f"{'='*60}")
    
    # Get all existing occupations
    occupations = {occ.occ_code.upper(): occ for occ in Occupation.objects.all()}
    
    # Verify all target codes exist
    for missing_code, target_code in CODE_MAPPINGS.items():
        if target_code not in occupations:
            print(f"ERROR: Target occupation code '{target_code}' not found in database!")
            return
    
    print(f"Code mappings:")
    for missing, target in CODE_MAPPINGS.items():
        target_name = occupations[target].occ_name
        print(f"  {missing} -> {target} ({target_name})")
    
    # Find candidates with NULL occupation
    affected_candidates = Candidate.objects.filter(occupation__isnull=True)
    
    mapped_count = 0
    updated_regno_count = 0
    not_found_codes = {}
    
    for candidate in affected_candidates:
        regno = candidate.registration_number
        if not regno:
            continue
            
        parts = regno.split('/')
        if len(parts) < 5:
            continue
            
        occ_code = parts[4].upper()
        
        if occ_code in CODE_MAPPINGS:
            target_code = CODE_MAPPINGS[occ_code]
            target_occupation = occupations[target_code]
            
            # Only update occupation field, keep registration number as is
            if not dry_run:
                candidate.occupation = target_occupation
                candidate.save(update_fields=['occupation'])
            
            mapped_count += 1
            
            # Show first few examples
            if mapped_count <= 10:
                print(f"  {regno} -> {target_code} ({target_occupation.occ_name})")
        elif occ_code not in occupations:
            # Track codes we can't map
            if occ_code not in not_found_codes:
                not_found_codes[occ_code] = []
            not_found_codes[occ_code].append(regno)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Candidates mapped: {mapped_count}")
    
    if not_found_codes:
        print(f"Codes not mapped (still missing):")
        for code, regnos in sorted(not_found_codes.items()):
            print(f"  {code}: {len(regnos)} candidates")
    
    if dry_run:
        print(f"\n*** DRY RUN - No changes made. Run with --apply to apply changes. ***")

if __name__ == '__main__':
    dry_run = '--apply' not in sys.argv
    
    if dry_run:
        print("\nRunning in DRY RUN mode. Use --apply to actually map occupations.")
    else:
        confirm = input("\nThis will UPDATE candidate occupation fields only. Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
    
    with transaction.atomic():
        map_missing_occupations(dry_run=dry_run)
        
        if dry_run:
            # Rollback in dry run
            transaction.set_rollback(True)
