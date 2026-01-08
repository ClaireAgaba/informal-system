#!/usr/bin/env python
"""
Investigate why candidates have occupation codes not in occupations table.
Check if these are old codes that were renamed or if there's a mapping issue.
"""

import os
import sys

# Add parent directory to path for Django imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emis.settings')
django.setup()

from candidates.models import Candidate
from occupations.models import Occupation

def investigate_missing_codes():
    """Investigate missing occupation codes"""
    
    # Find all candidates with NULL occupation
    affected_candidates = Candidate.objects.filter(occupation__isnull=True)
    
    # Get all existing occupation codes
    existing_codes = set(occ.occ_code.upper() for occ in Occupation.objects.all())
    
    # Collect codes from registration numbers
    missing_codes = {}
    no_code_count = 0
    
    for candidate in affected_candidates:
        regno = candidate.registration_number
        if not regno:
            no_code_count += 1
            continue
            
        parts = regno.split('/')
        if len(parts) >= 5:
            occ_code = parts[4].upper()
            if occ_code not in existing_codes:
                if occ_code not in missing_codes:
                    missing_codes[occ_code] = []
                missing_codes[occ_code].append(regno)
        else:
            no_code_count += 1
    
    print(f"\n{'='*60}")
    print(f"Missing Occupation Codes Investigation")
    print(f"{'='*60}")
    print(f"Total candidates with NULL occupation: {affected_candidates.count()}")
    print(f"Candidates with no extractable code: {no_code_count}")
    print(f"Unique missing codes: {len(missing_codes)}")
    
    print(f"\nExisting occupation codes (first 20):")
    print(f"  {sorted(existing_codes)[:20]}")
    
    print(f"\nMissing codes with candidate counts:")
    for code, regnos in sorted(missing_codes.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {code}: {len(regnos)} candidates")
        if len(regnos) <= 3:
            for regno in regnos:
                print(f"    - {regno}")
    
    # Check if any missing codes might be variations of existing codes
    print(f"\nPotential matches (similar codes):")
    for missing_code in missing_codes:
        for existing_code in existing_codes:
            if missing_code[:2] == existing_code[:2] or missing_code[-2:] == existing_code[-2:]:
                print(f"  {missing_code} might be related to {existing_code}")
    
    # Show a few sample registration numbers for each missing code
    print(f"\nSample registration numbers for missing codes:")
    for code, regnos in sorted(missing_codes.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        print(f"\n  {code} (showing first 5 of {len(regnos)}):")
        for regno in regnos[:5]:
            print(f"    - {regno}")

if __name__ == '__main__':
    investigate_missing_codes()
