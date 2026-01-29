
import os
import sys
import django
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emis.settings')
django.setup()

from stats.utils import calculate_series_statistics
from assessment_series.models import AssessmentSeries
from candidates.models import Candidate, CandidateEnrollment
from results.models import ModularResult
from assessment_centers.models import AssessmentCenter

def repro_discrepancy():
    print("Reproduction Script Started...")
    
    # 1. Create Data
    # Cleaning up previous run
    AssessmentSeries.objects.filter(name="Repro Series").delete()
    
    # 1. Create Data
    series = AssessmentSeries.objects.create(name="Repro Series", start_date="2026-01-01", end_date="2026-01-31", date_of_release="2026-02-01")
    center = AssessmentCenter.objects.first()
    
    # Candidate 1: Normal (Business Sector)
    # Assume occupation exists, let's just use first one
    from occupations.models import Occupation, OccupationLevel, OccupationModule
    occ = Occupation.objects.first()
    
    # Create Level and Module
    level, _ = OccupationLevel.objects.get_or_create(occupation=occ, level_name="Level 1")
    module, _ = OccupationModule.objects.get_or_create(occupation=occ, level=level, module_code='MOD1', defaults={'module_name': 'Module 1'})
    module2, _ = OccupationModule.objects.get_or_create(occupation=occ, level=level, module_code='MOD2', defaults={'module_name': 'Module 2'})
    
    c1 = Candidate.objects.create(
        gender='male', 
        occupation=occ, 
        registration_category='modular',
        date_of_birth="2000-01-01",
        entry_year=2026,
        intake='M',
        contact="0700000001",
        assessment_center=center
    )
    CandidateEnrollment.objects.create(candidate=c1, assessment_series=series)
    ModularResult.objects.create(candidate=c1, assessment_series=series, module=module, mark=80) # Sat & Passed
    
    # Candidate 2: Missing Occupation (Uncategorized)
    c2 = Candidate.objects.create(
        gender='female', 
        occupation=None, 
        registration_category='modular',
        date_of_birth="2000-01-02",
        entry_year=2026,
        intake='M',
        contact="0700000002",
        assessment_center=center
    )
    CandidateEnrollment.objects.create(candidate=c2, assessment_series=series)
    ModularResult.objects.create(candidate=c2, assessment_series=series, module=module2, mark=40) # Sat & Failed
    
    print(f"Created Series {series.id}. Candidates: 2 (1 Normal, 1 Uncategorized). Both Sat.")
    
    # 2. Run Stats
    stats = calculate_series_statistics(series.id)
    
    # 3. Analyze Overview
    overview = stats['overview']
    sat_total_overview = overview['sat']
    print(f"Overview Sat: {sat_total_overview} (Expected 2)")
    
    # 4. Analyze Sector Stats
    sector_stats = stats['sector_stats']
    sat_total_sector = sum(s['sat'] for s in sector_stats)
    print(f"Sector Breakdown Sum Sat: {sat_total_sector} (Expected 2)")
    
    print("Sectors found:")
    for s in sector_stats:
        print(f" - {s['name']}: {s['sat']} sat")
        
    # 5. Analyze Occupation Stats
    occ_stats = stats['occupation_stats']
    # Filter only summaries or sum individuals?
    # Logic in utils: 'is_sector_summary' items are summaries. Individual items are not.
    # We should sum individual occupations to avoid double counting if we sum everything.
    # Or just check the list content.
    
    print("Occupations found:")
    sat_total_occ = 0
    for o in occ_stats:
        print(f" - {o['occupation_name']} ({o['sector_name']}): {o['sat']} sat {'[SUMMARY]' if o.get('is_sector_summary') else ''}")
        if not o.get('is_sector_summary'):
            sat_total_occ += o['sat']
            
    print(f"Occupation Breakdown Sum Sat: {sat_total_occ} (Expected 2)")
    
    # 6. Check Discrepancy
    if sat_total_overview != sat_total_sector:
        print("FAIL: Sector Mismatch!")
    else:
        print("PASS: Sector Match")
        
    if sat_total_overview != sat_total_occ:
         print("FAIL: Occupation Mismatch!")
    else:
        print("PASS: Occupation Match")

    # Cleanup
    # c1.delete(); c2.delete(); series.delete() 
    # (Leaving for debug if needed)

if __name__ == '__main__':
    repro_discrepancy()
