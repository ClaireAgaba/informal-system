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
    Detailed results for a specific assessment series with candidate-centric metrics.
    Metrics: Enrolled, Missing, Sat, Passed, Failed.
    Pass Criteria: Candidate must pass ALL sat papers/modules.
    """
    from .utils import calculate_series_statistics
    
    # Filter by Centers if provided
    center_ids_param = request.query_params.get('center_ids')
    center_ids = [int(id) for id in center_ids_param.split(',')] if center_ids_param else []
    
    stats_data = calculate_series_statistics(series_id, center_ids)
    
    if not stats_data:
        return Response({'error': 'Series not found'}, status=404)
        
    return Response(stats_data)
@api_view(['GET'])
@permission_classes([AllowAny])
def special_needs_analytics(request):
    """
    Comprehensive analytics for special needs candidates with gender-based pass rates
    Optional query params: series_id
    """
    from assessment_series.models import AssessmentSeries
    from configurations.models import NatureOfDisability
    from results.models import ModularResult, FormalResult, WorkersPasResult
    
    series_id = request.query_params.get('series_id')
    
    # Get all results (optionally filtered by series)
    if series_id:
        all_results = list(ModularResult.objects.filter(assessment_series_id=series_id).select_related('candidate', 'candidate__nature_of_disability')) + \
                      list(FormalResult.objects.filter(assessment_series_id=series_id).select_related('candidate', 'candidate__nature_of_disability')) + \
                      list(WorkersPasResult.objects.filter(assessment_series_id=series_id).select_related('candidate', 'candidate__nature_of_disability'))
    else:
        all_results = list(ModularResult.objects.all().select_related('candidate', 'candidate__nature_of_disability')) + \
                      list(FormalResult.objects.all().select_related('candidate', 'candidate__nature_of_disability')) + \
                      list(WorkersPasResult.objects.all().select_related('candidate', 'candidate__nature_of_disability'))
    
    # Filter to only special needs candidates
    special_needs_results = [r for r in all_results if r.candidate.has_disability]
    
    # Calculate overall special needs statistics
    special_needs_male = [r for r in special_needs_results if r.candidate.gender == 'male']
    special_needs_female = [r for r in special_needs_results if r.candidate.gender == 'female']
    
    # Count passed results (only count results with actual marks)
    def is_passed(result):
        # Skip results without marks
        if result.mark is None:
            return False
            
        if isinstance(result, ModularResult):
            return result.mark >= 65
        elif isinstance(result, FormalResult):
            return (result.type == 'theory' and result.mark >= 50) or (result.type == 'practical' and result.mark >= 65)
        elif isinstance(result, WorkersPasResult):
            return result.mark >= 65
        return False
    
    male_passed = sum(1 for r in special_needs_male if is_passed(r))
    female_passed = sum(1 for r in special_needs_female if is_passed(r))
    total_passed = male_passed + female_passed
    
    overview = {
        'total': len(special_needs_results),
        'male': len(special_needs_male),
        'female': len(special_needs_female),
        'male_passed': male_passed,
        'female_passed': female_passed,
        'total_passed': total_passed,
        'male_pass_rate': round((male_passed / len(special_needs_male) * 100), 2) if len(special_needs_male) > 0 else 0,
        'female_pass_rate': round((female_passed / len(special_needs_female) * 100), 2) if len(special_needs_female) > 0 else 0,
        'pass_rate': round((total_passed / len(special_needs_results) * 100), 2) if len(special_needs_results) > 0 else 0
    }
    
    # By disability type with comprehensive metrics
    disability_breakdown = []
    for disability in NatureOfDisability.objects.all():
        disability_results = [r for r in special_needs_results if r.candidate.nature_of_disability == disability]
        
        if not disability_results:
            continue
        
        dis_male = [r for r in disability_results if r.candidate.gender == 'male']
        dis_female = [r for r in disability_results if r.candidate.gender == 'female']
        
        dis_male_passed = sum(1 for r in dis_male if is_passed(r))
        dis_female_passed = sum(1 for r in dis_female if is_passed(r))
        dis_total_passed = dis_male_passed + dis_female_passed
        
        disability_breakdown.append({
            'name': disability.name,
            'total': len(disability_results),
            'male': len(dis_male),
            'female': len(dis_female),
            'male_passed': dis_male_passed,
            'female_passed': dis_female_passed,
            'total_passed': dis_total_passed,
            'male_pass_rate': round((dis_male_passed / len(dis_male) * 100), 2) if len(dis_male) > 0 else 0,
            'female_pass_rate': round((dis_female_passed / len(dis_female) * 100), 2) if len(dis_female) > 0 else 0,
            'pass_rate': round((dis_total_passed / len(disability_results) * 100), 2) if len(disability_results) > 0 else 0
        })
    
    # By sector with comprehensive metrics
    from occupations.models import Sector
    special_needs_by_sector = []
    for sector in Sector.objects.all():
        # Get results where candidate's occupation belongs to this sector
        sector_results = [r for r in special_needs_results if 
                         r.candidate.occupation and r.candidate.occupation.sector == sector]
        
        if not sector_results:
            continue
        
        sector_male = [r for r in sector_results if r.candidate.gender == 'male']
        sector_female = [r for r in sector_results if r.candidate.gender == 'female']
        
        sector_male_passed = sum(1 for r in sector_male if is_passed(r))
        sector_female_passed = sum(1 for r in sector_female if is_passed(r))
        sector_total_passed = sector_male_passed + sector_female_passed
        
        special_needs_by_sector.append({
            'sector_name': sector.name,
            'total': len(sector_results),
            'male': len(sector_male),
            'female': len(sector_female),
            'male_passed': sector_male_passed,
            'female_passed': sector_female_passed,
            'total_passed': sector_total_passed,
            'male_pass_rate': round((sector_male_passed / len(sector_male) * 100), 2) if len(sector_male) > 0 else 0,
            'female_pass_rate': round((sector_female_passed / len(sector_female) * 100), 2) if len(sector_female) > 0 else 0,
            'pass_rate': round((sector_total_passed / len(sector_results) * 100), 2) if len(sector_results) > 0 else 0
        })
    
    # REFUGEE STATISTICS
    # Filter to only refugee candidates
    refugee_results = [r for r in all_results if r.candidate.is_refugee]
    
    # Calculate overall refugee statistics
    refugee_male = [r for r in refugee_results if r.candidate.gender == 'male']
    refugee_female = [r for r in refugee_results if r.candidate.gender == 'female']
    
    refugee_male_passed = sum(1 for r in refugee_male if is_passed(r))
    refugee_female_passed = sum(1 for r in refugee_female if is_passed(r))
    refugee_total_passed = refugee_male_passed + refugee_female_passed
    
    refugee_overview = {
        'total': len(refugee_results),
        'male': len(refugee_male),
        'female': len(refugee_female),
        'male_passed': refugee_male_passed,
        'female_passed': refugee_female_passed,
        'total_passed': refugee_total_passed,
        'male_pass_rate': round((refugee_male_passed / len(refugee_male) * 100), 2) if len(refugee_male) > 0 else 0,
        'female_pass_rate': round((refugee_female_passed / len(refugee_female) * 100), 2) if len(refugee_female) > 0 else 0,
        'pass_rate': round((refugee_total_passed / len(refugee_results) * 100), 2) if len(refugee_results) > 0 else 0
    }
    
    # Refugee by sector
    refugee_by_sector = []
    for sector in Sector.objects.all():
        # Get results where candidate's occupation belongs to this sector
        sector_results = [r for r in refugee_results if 
                         r.candidate.occupation and r.candidate.occupation.sector == sector]
        
        if not sector_results:
            continue
        
        sector_male = [r for r in sector_results if r.candidate.gender == 'male']
        sector_female = [r for r in sector_results if r.candidate.gender == 'female']
        
        sector_male_passed = sum(1 for r in sector_male if is_passed(r))
        sector_female_passed = sum(1 for r in sector_female if is_passed(r))
        sector_total_passed = sector_male_passed + sector_female_passed
        
        refugee_by_sector.append({
            'sector_name': sector.name,
            'total': len(sector_results),
            'male': len(sector_male),
            'female': len(sector_female),
            'male_passed': sector_male_passed,
            'female_passed': sector_female_passed,
            'total_passed': sector_total_passed,
            'male_pass_rate': round((sector_male_passed / len(sector_male) * 100), 2) if len(sector_male) > 0 else 0,
            'female_pass_rate': round((sector_female_passed / len(sector_female) * 100), 2) if len(sector_female) > 0 else 0,
            'pass_rate': round((sector_total_passed / len(sector_results) * 100), 2) if len(sector_results) > 0 else 0
        })
    
    return Response({
        'special_needs': {
            'overview': overview,
            'by_disability_type': disability_breakdown,
            'by_sector': special_needs_by_sector
        },
        'refugee': {
            'overview': refugee_overview,
            'by_sector': refugee_by_sector
        }
    })


