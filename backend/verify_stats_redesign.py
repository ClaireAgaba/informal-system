
import os
import sys
import django

# Setup Django
sys.path.append('/home/bfh/code/informal-system/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'emis.settings')
django.setup()

from django.conf import settings
from rest_framework.test import APIRequestFactory
from stats.views import assessment_series_results
from stats.excel_export import export_series_excel
from assessment_series.models import AssessmentSeries

def verify_stats():
    # Find a series
    series = AssessmentSeries.objects.first()
    if not series:
        print("No Assessment Series found. Cannot verify.")
        return

    print(f"Verifying Stats for Series: {series.name} (ID: {series.id})")

    factory = APIRequestFactory()
    request = factory.get(f'/api/statistics/series/{series.id}/results/')

    try:
        response = assessment_series_results(request, series_id=series.id)
        if response.status_code != 200:
            print(f"FAILED: API returned status {response.status_code}")
            print(response.data)
            return

        data = response.data
        print("API Response Structure Verified.")
        
        # Check Overview Keys
        overview = data.get('overview')
        required_keys = ['enrolled', 'missing', 'sat', 'passed', 'failed', 'male_sat', 'female_sat', 'missing_rate', 'sat_rate']
        missing_keys = [k for k in required_keys if k not in overview]
        
        if missing_keys:
            print(f"FAILED: Overview missing keys: {missing_keys}")
        else:
            print(f"PASSED: Overview keys present.")
            print("Overview Data:")
            for k, v in overview.items():
                print(f"  {k}: {v}")

        # Basic Logic Check
        if overview['enrolled'] != (overview['missing'] + overview['sat']):
            print("WARNING: Enrolled != Missing + Sat (Might be floating point or logic edge case?)")
            print(f"  {overview['enrolled']} vs {overview['missing'] + overview['sat']}")
        else:
            print("PASSED: Enrolled == Missing + Sat")
            
        # Verify Rates
        if 'missing_rate' in overview and overview['enrolled'] > 0:
             calc_miss = round(overview['missing'] / overview['enrolled'] * 100, 2)
             if abs(overview['missing_rate'] - calc_miss) > 0.1:
                  print(f"WARNING: Calculated missing rate {calc_miss} != API {overview['missing_rate']}")
             else:
                  print(f"PASSED: Missing Rate Verified ({overview['missing_rate']}%)")
        
        if 'sat_rate' in overview and overview['enrolled'] > 0:
             calc_sat = round(overview['sat'] / overview['enrolled'] * 100, 2)
             if abs(overview['sat_rate'] - calc_sat) > 0.1:
                  print(f"WARNING: Calculated sat rate {calc_sat} != API {overview['sat_rate']}")
             else:
                  print(f"PASSED: Sat Rate Verified ({overview['sat_rate']}%)")

        if overview['sat'] != (overview['passed'] + overview['failed']):
             print("WARNING: Sat != Passed + Failed")
             print(f"  {overview['sat']} vs {overview['passed'] + overview['failed']}")
        else:
             print("PASSED: Sat == Passed + Failed")


        # Verify Excel Export
        print("\nVerifying Excel Export...")
        excel_request = factory.get(f'/api/statistics/series/{series.id}/export-excel/')
        excel_response = export_series_excel(excel_request, series_id=series.id)
        
        if excel_response.status_code == 200:
            print("PASSED: Excel export returned 200 OK")
            print(f"Content Type: {excel_response['Content-Type']}")
            if len(excel_response.content) > 0:
                print(f"PASSED: Excel content length > 0 bytes ({len(excel_response.content)} bytes)")
            else:
                print("FAILED: Excel content is empty")
        else:
             print(f"FAILED: Excel export returned {excel_response.status_code}")

    except Exception as e:
        print(f"Method failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verify_stats()
