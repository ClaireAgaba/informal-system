from assessment_series.models import AssessmentSeries
from candidates.models import CandidateEnrollment
from django.db.models import Count

print("=== Assessment Series ===")
series = AssessmentSeries.objects.all()
print(f"Total series: {series.count()}")
for s in series:
    print(f"  - {s.name} (ID: {s.id}, Start: {s.start_date})")

print("\n=== Enrollments by Series ===")
enrollments = CandidateEnrollment.objects.values('assessment_series_id').annotate(count=Count('id'))
for e in enrollments:
    series_id = e['assessment_series_id']
    count = e['count']
    try:
        series_name = AssessmentSeries.objects.get(id=series_id).name
        print(f"  - Series {series_id} ({series_name}): {count} enrollments")
    except:
        print(f"  - Series {series_id}: {count} enrollments")

print("\n=== Testing API Logic ===")
series_ids = list(AssessmentSeries.objects.values_list('id', flat=True))
print(f"Series IDs: {series_ids}")

enrollment_stats = {}
enrollments_with_gender = CandidateEnrollment.objects.filter(
    assessment_series_id__in=series_ids
).select_related('candidate').values(
    'assessment_series_id', 'candidate__gender'
).annotate(count=Count('id'))

for enrollment in enrollments_with_gender:
    series_id = enrollment['assessment_series_id']
    gender = enrollment['candidate__gender']
    if series_id not in enrollment_stats:
        enrollment_stats[series_id] = {'total': 0, 'male': 0, 'female': 0}
    enrollment_stats[series_id]['total'] += enrollment['count']
    if gender == 'male':
        enrollment_stats[series_id]['male'] += enrollment['count']
    elif gender == 'female':
        enrollment_stats[series_id]['female'] += enrollment['count']

print(f"\nEnrollment stats: {enrollment_stats}")
