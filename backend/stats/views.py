"""
Statistics API Views

Provides aggregated statistics and analytics for the EMIS system
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Count, Q
from candidates.models import Candidate
from occupations.models import Occupation
from assessment_centers.models import AssessmentCenter
from results.models import ModularResult, FormalResult, WorkersPasResult


@api_view(['GET'])
@permission_classes([AllowAny])
def overall_statistics(request):
    """
    Get overall system statistics
    """
    # Count totals
    total_candidates = Candidate.objects.count()
    total_occupations = Occupation.objects.count()
    total_centers = AssessmentCenter.objects.count()
    
    # Count all results
    total_results = (
        ModularResult.objects.count() +
        FormalResult.objects.count() +
        WorkersPasResult.objects.count()
    )
    
    return Response({
        'total_candidates': total_candidates,
        'total_occupations': total_occupations,
        'total_centers': total_centers,
        'total_results': total_results,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def candidates_by_gender(request):
    """
    Get candidates grouped by gender
    """
    stats = Candidate.objects.aggregate(
        male=Count('id', filter=Q(gender='male')),
        female=Count('id', filter=Q(gender='female')),
        other=Count('id', filter=Q(gender='other')),
    )
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([AllowAny])
def candidates_by_category(request):
    """
    Get candidates grouped by registration category
    """
    stats = Candidate.objects.aggregate(
        modular=Count('id', filter=Q(registration_category='modular')),
        formal=Count('id', filter=Q(registration_category='formal')),
        workers_pas=Count('id', filter=Q(registration_category='workers_pas')),
    )
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([AllowAny])
def candidates_by_special_needs(request):
    """
    Get candidates grouped by special needs status
    """
    stats = Candidate.objects.aggregate(
        with_special_needs=Count('id', filter=Q(has_disability=True)),
        without_special_needs=Count('id', filter=Q(has_disability=False)),
    )
    
    # Break down by gender
    gender_stats = {
        'male_with_special_needs': Candidate.objects.filter(
            has_disability=True, gender='male'
        ).count(),
        'female_with_special_needs': Candidate.objects.filter(
            has_disability=True, gender='female'
        ).count(),
    }
    
    return Response({
        **stats,
        **gender_stats
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def assessment_series_list(request):
    """
    Get all assessment series with basic statistics - OPTIMIZED VERSION
    """
    from assessment_series.models import AssessmentSeries
    from django.db.models import Count, Q, Prefetch
    
    # Fetch all series with prefetched data in a single query
    series = AssessmentSeries.objects.all().order_by('-start_date')
    
    # If there are no series, return empty list
    if not series.exists():
        return Response([])
    
    # Get all series IDs
    series_ids = list(series.values_list('id', flat=True))
    
    # Fetch enrollment counts by series and gender in ONE query
    from candidates.models import CandidateEnrollment
    enrollment_stats = {}
    enrollments = CandidateEnrollment.objects.filter(
        assessment_series_id__in=series_ids
    ).select_related('candidate').values(
        'assessment_series_id', 'candidate__gender'
    ).annotate(count=Count('id'))
    
    for enrollment in enrollments:
        series_id = enrollment['assessment_series_id']
        gender = enrollment['candidate__gender']
        if series_id not in enrollment_stats:
            enrollment_stats[series_id] = {'total': 0, 'male': 0, 'female': 0}
        enrollment_stats[series_id]['total'] += enrollment['count']
        if gender == 'male':
            enrollment_stats[series_id]['male'] += enrollment['count']
        elif gender == 'female':
            enrollment_stats[series_id]['female'] += enrollment['count']
    
    # Fetch result counts by series in FOUR queries (one per result type)
    modular_counts = {}
    for series_id, total, passing in ModularResult.objects.filter(
        assessment_series_id__in=series_ids
    ).values('assessment_series_id').annotate(
        total=Count('id'),
        passing=Count('id', filter=Q(mark__gte=65))
    ).values_list('assessment_series_id', 'total', 'passing'):
        modular_counts[series_id] = (total, passing)
    
    formal_theory_counts = {}
    for series_id, total, passing in FormalResult.objects.filter(
        assessment_series_id__in=series_ids,
        type='theory'
    ).values('assessment_series_id').annotate(
        total=Count('id'),
        passing=Count('id', filter=Q(mark__gte=50))
    ).values_list('assessment_series_id', 'total', 'passing'):
        formal_theory_counts[series_id] = (total, passing)
    
    formal_practical_counts = {}
    for series_id, total, passing in FormalResult.objects.filter(
        assessment_series_id__in=series_ids,
        type='practical'
    ).values('assessment_series_id').annotate(
        total=Count('id'),
        passing=Count('id', filter=Q(mark__gte=65))
    ).values_list('assessment_series_id', 'total', 'passing'):
        formal_practical_counts[series_id] = (total, passing)
    
    workers_counts = {}
    for series_id, total, passing in WorkersPasResult.objects.filter(
        assessment_series_id__in=series_ids
    ).values('assessment_series_id').annotate(
        total=Count('id'),
        passing=Count('id', filter=Q(mark__gte=65))
    ).values_list('assessment_series_id', 'total', 'passing'):
        workers_counts[series_id] = (total, passing)
    
    # Build response
    series_stats = []
    for s in series:
        stats = enrollment_stats.get(s.id, {'total': 0, 'male': 0, 'female': 0})
        
        # Calculate total results and passing
        mod = modular_counts.get(s.id, (0, 0))
        ft = formal_theory_counts.get(s.id, (0, 0))
        fp = formal_practical_counts.get(s.id, (0, 0))
        wp = workers_counts.get(s.id, (0, 0))
        
        total_results = mod[0] + ft[0] + fp[0] + wp[0]
        total_passing = mod[1] + ft[1] + fp[1] + wp[1]
        
        pass_rate = (total_passing / total_results * 100) if total_results > 0 else 0
        
        series_stats.append({
            'id': s.id,
            'name': s.name,
            'start_date': s.start_date,
            'end_date': s.end_date,
            'year': s.start_date.year if s.start_date else None,
            'total_candidates': stats['total'],
            'male': stats['male'],
            'female': stats['female'],
            'total_results': total_results,
            'pass_rate': round(pass_rate, 2)
        })
    
    return Response(series_stats)


@api_view(['GET'])
@permission_classes([AllowAny])
def assessment_series_results(request, series_id):
    """
    Detailed results for a specific assessment series with gender breakdown
    """
    from assessment_series.models import AssessmentSeries
    from django.db.models import Count, Q, Avg
    
    try:
        series = AssessmentSeries.objects.get(id=series_id)
    except AssessmentSeries.DoesNotExist:
        return Response({'error': 'Series not found'}, status=404)
    
    # Get all candidates enrolled in this series
    enrolled_candidates = Candidate.objects.filter(
        enrollments__assessment_series=series
    ).distinct()
    
    male_candidates = enrolled_candidates.filter(gender='male')
    female_candidates = enrolled_candidates.filter(gender='female')
    
    # Calculate overall pass rates
    def calc_pass_rate(queryset, result_model, is_theory=False):
        total = result_model.objects.filter(
            assessment_series=series,
            candidate__in=queryset
        )
        if is_theory:
            total = total.filter(type='theory')
            passing = total.filter(mark__gte=50).count()
        else:
            if hasattr(result_model, 'type'):
                total = total.filter(type='practical')
            passing = total.filter(mark__gte=65).count()
        
        total_count = total.count()
        return (passing / total_count * 100) if total_count > 0 else 0
    
    # Overall stats
    total_results = (
        ModularResult.objects.filter(assessment_series=series).count() +
        FormalResult.objects.filter(assessment_series=series).count() +
        WorkersPasResult.objects.filter(assessment_series=series).count()
    )
    
    # Calculate pass rates by gender
    male_pass_rate = (
        calc_pass_rate(male_candidates, ModularResult) +
        calc_pass_rate(male_candidates, FormalResult, is_theory=True) +
        calc_pass_rate(male_candidates, FormalResult, is_theory=False) +
        calc_pass_rate(male_candidates, WorkersPasResult)
    ) / 4
    
    female_pass_rate = (
        calc_pass_rate(female_candidates, ModularResult) +
        calc_pass_rate(female_candidates, FormalResult, is_theory=True) +
        calc_pass_rate(female_candidates, FormalResult, is_theory=False) +
        calc_pass_rate(female_candidates, WorkersPasResult)
    ) / 4
    
    overall_pass_rate = (male_pass_rate + female_pass_rate) / 2
    
    # By category
    category_stats = {}
    for cat in ['modular', 'formal', 'workers_pas']:
        cat_candidates = enrolled_candidates.filter(registration_category=cat)
        male_cat = cat_candidates.filter(gender='male').count()
        female_cat = cat_candidates.filter(gender='female').count()
        
        category_stats[cat] = {
            'total': cat_candidates.count(),
            'male': male_cat,
            'female': female_cat,
            'pass_rate': 0  # Simplified for now
        }
    
    # Grade distribution (simplified - count all grades)
    grade_dist = {}
    all_results = list(ModularResult.objects.filter(assessment_series=series)) + \
                  list(FormalResult.objects.filter(assessment_series=series)) + \
                  list(WorkersPasResult.objects.filter(assessment_series=series))
    
    for result in all_results:
        grade = result.grade
        if grade:
            if grade not in grade_dist:
                grade_dist[grade] = {'total': 0, 'male': 0, 'female': 0}
            grade_dist[grade]['total'] += 1
            if result.candidate.gender == 'male':
                grade_dist[grade]['male'] += 1
            elif result.candidate.gender == 'female':
                grade_dist[grade]['female'] += 1
    
    # By occupation
    occupation_stats = []
    occupations = Occupation.objects.filter(
        candidates__in=enrolled_candidates
    ).distinct()
    
    for occ in occupations:
        occ_candidates = enrolled_candidates.filter(occupation=occ)
        occ_male = occ_candidates.filter(gender='male').count()
        occ_female = occ_candidates.filter(gender='female').count()
        
        occupation_stats.append({
            'occupation_name': occ.occ_name,
            'occupation_code': occ.occ_code,
            'total_candidates': occ_candidates.count(),
            'male': occ_male,
            'female': occ_female,
            'pass_rate': 0,  # Simplified for now
            'male_pass_rate': 0,
            'female_pass_rate': 0
        })
    
    return Response({
        'series': {
            'id': series.id,
            'name': series.name,
            'start_date': series.start_date,
            'end_date': series.end_date
        },
        'overview': {
            'total_candidates': enrolled_candidates.count(),
            'male': male_candidates.count(),
            'female': female_candidates.count(),
            'total_results': total_results,
            'pass_rate': round(overall_pass_rate, 2),
            'male_pass_rate': round(male_pass_rate, 2),
            'female_pass_rate': round(female_pass_rate, 2)
        },
        'by_category': category_stats,
        'grade_distribution': grade_dist,
        'by_occupation': occupation_stats
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def special_needs_analytics(request):
    """
    Analytics for special needs and refugee candidates
    Optional query params: series_id
    """
    from assessment_series.models import AssessmentSeries
    
    series_id = request.query_params.get('series_id')
    
    # Base querysets
    special_needs_candidates = Candidate.objects.filter(has_disability=True)
    refugee_candidates = Candidate.objects.filter(is_refugee=True)
    
    # Filter by series if provided
    if series_id:
        special_needs_candidates = special_needs_candidates.filter(
            enrollments__assessment_series_id=series_id
        ).distinct()
        refugee_candidates = refugee_candidates.filter(
            enrollments__assessment_series_id=series_id
        ).distinct()
    
    # Special Needs Statistics
    special_needs_male = special_needs_candidates.filter(gender='male').count()
    special_needs_female = special_needs_candidates.filter(gender='female').count()
    
    # By disability type
    disability_breakdown = []
    from configurations.models import NatureOfDisability
    for disability in NatureOfDisability.objects.all():
        candidates_with = special_needs_candidates.filter(nature_of_disability=disability)
        disability_breakdown.append({
            'name': disability.name,
            'count': candidates_with.count(),
            'male': candidates_with.filter(gender='male').count(),
            'female': candidates_with.filter(gender='female').count()
        })
    
    # By series for special needs
    special_needs_by_series = []
    for series in AssessmentSeries.objects.all().order_by('-start_date')[:10]:
        series_candidates = special_needs_candidates.filter(
            enrollments__assessment_series=series
        ).distinct()
        
        special_needs_by_series.append({
            'series_id': series.id,
            'series_name': series.name,
            'total': series_candidates.count(),
            'male': series_candidates.filter(gender='male').count(),
            'female': series_candidates.filter(gender='female').count(),
            'pass_rate': 0  # Simplified for now
        })
    
    # Refugee Statistics
    refugee_male = refugee_candidates.filter(gender='male').count()
    refugee_female = refugee_candidates.filter(gender='female').count()
    
    # By nationality
    nationality_breakdown = []
    nationalities = refugee_candidates.values_list('nationality', flat=True).distinct()
    for nat in nationalities:
        nat_candidates = refugee_candidates.filter(nationality=nat)
        nationality_breakdown.append({
            'nationality': nat,
            'count': nat_candidates.count(),
            'male': nat_candidates.filter(gender='male').count(),
            'female': nat_candidates.filter(gender='female').count()
        })
    
    # By series for refugees
    refugee_by_series = []
    for series in AssessmentSeries.objects.all().order_by('-start_date')[:10]:
        series_candidates = refugee_candidates.filter(
            enrollments__assessment_series=series
        ).distinct()
        
        refugee_by_series.append({
            'series_id': series.id,
            'series_name': series.name,
            'total': series_candidates.count(),
            'male': series_candidates.filter(gender='male').count(),
            'female': series_candidates.filter(gender='female').count(),
            'pass_rate': 0  # Simplified for now
        })
    
    return Response({
        'special_needs': {
            'total': special_needs_candidates.count(),
            'male': special_needs_male,
            'female': special_needs_female,
            'by_disability_type': disability_breakdown,
            'by_series': special_needs_by_series
        },
        'refugee': {
            'total': refugee_candidates.count(),
            'male': refugee_male,
            'female': refugee_female,
            'by_nationality': nationality_breakdown,
            'by_series': refugee_by_series
        }
    })

