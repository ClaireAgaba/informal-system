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
    
    # Get enrolled candidates with gender info
    from candidates.models import CandidateEnrollment
    enrollments = CandidateEnrollment.objects.filter(
        assessment_series_id=series_id
    ).select_related('candidate')
    
    total_candidates = enrollments.count()
    male_candidates = enrollments.filter(candidate__gender='male').count()
    female_candidates = enrollments.filter(candidate__gender='female').count()
    
    # Calculate overall pass rates by gender
    # Get all results with candidate gender information
    male_results_count = 0
    male_passing_count = 0
    female_results_count = 0
    female_passing_count = 0
    
    # Modular results by gender
    for result in ModularResult.objects.filter(
        assessment_series_id=series_id
    ).select_related('candidate'):
        gender = result.candidate.gender
        if gender == 'male':
            male_results_count += 1
            if result.mark >= 65:
                male_passing_count += 1
        elif gender == 'female':
            female_results_count += 1
            if result.mark >= 65:
                female_passing_count += 1
    
    # Formal results by gender
    for result in FormalResult.objects.filter(
        assessment_series_id=series_id
    ).select_related('candidate'):
        gender = result.candidate.gender
        passing_mark = 50 if result.type == 'theory' else 65
        if gender == 'male':
            male_results_count += 1
            if result.mark >= passing_mark:
                male_passing_count += 1
        elif gender == 'female':
            female_results_count += 1
            if result.mark >= passing_mark:
                female_passing_count += 1
    
    # Workers PAS results by gender
    for result in WorkersPasResult.objects.filter(
        assessment_series_id=series_id
    ).select_related('candidate'):
        gender = result.candidate.gender
        if gender == 'male':
            male_results_count += 1
            if result.mark >= 65:
                male_passing_count += 1
        elif gender == 'female':
            female_results_count += 1
            if result.mark >= 65:
                female_passing_count += 1
    
    # Calculate pass rates
    male_pass_rate = (male_passing_count / male_results_count * 100) if male_results_count > 0 else 0
    female_pass_rate = (female_passing_count / female_results_count * 100) if female_results_count > 0 else 0
    overall_pass_rate = ((male_passing_count + female_passing_count) / (male_results_count + female_results_count) * 100) if (male_results_count + female_results_count) > 0 else 0
    
    # Build overview statistics
    overview = {
        'total_candidates': total_candidates,
        'male': male_candidates,
        'female': female_candidates,
        'total_results': male_results_count + female_results_count,
        'pass_rate': round(overall_pass_rate, 2),
        'male_pass_rate': round(male_pass_rate, 2),
        'female_pass_rate': round(female_pass_rate, 2),
    }
    
    # Get enrolled candidates for category/occupation stats
    enrolled_candidates = Candidate.objects.filter(
        enrollments__assessment_series=series
    ).distinct()
    
    # By category - comprehensive gender-based metrics
    category_stats = {}
    
    # Modular category
    modular_results = ModularResult.objects.filter(assessment_series_id=series_id).select_related('candidate')
    modular_total = modular_results.count()
    modular_male_results = modular_results.filter(candidate__gender='male')
    modular_female_results = modular_results.filter(candidate__gender='female')
    
    modular_male = modular_male_results.count()
    modular_female = modular_female_results.count()
    modular_male_passed = modular_male_results.filter(mark__gte=65).count()
    modular_female_passed = modular_female_results.filter(mark__gte=65).count()
    modular_total_passed = modular_male_passed + modular_female_passed
    
    category_stats['modular'] = {
        'total': modular_total,
        'male': modular_male,
        'female': modular_female,
        'male_passed': modular_male_passed,
        'female_passed': modular_female_passed,
        'total_passed': modular_total_passed,
        'male_pass_rate': round((modular_male_passed / modular_male * 100), 2) if modular_male > 0 else 0,
        'female_pass_rate': round((modular_female_passed / modular_female * 100), 2) if modular_female > 0 else 0,
        'pass_rate': round((modular_total_passed / modular_total * 100), 2) if modular_total > 0 else 0
    }
    
    # Formal category (both theory and practical)
    formal_results = FormalResult.objects.filter(assessment_series_id=series_id).select_related('candidate')
    formal_total = formal_results.count()
    formal_male_results = formal_results.filter(candidate__gender='male')
    formal_female_results = formal_results.filter(candidate__gender='female')
    
    formal_male = formal_male_results.count()
    formal_female = formal_female_results.count()
    
    # Calculate passing: theory ≥50, practical ≥65
    formal_male_passed = (
        formal_male_results.filter(type='theory', mark__gte=50).count() +
        formal_male_results.filter(type='practical', mark__gte=65).count()
    )
    formal_female_passed = (
        formal_female_results.filter(type='theory', mark__gte=50).count() +
        formal_female_results.filter(type='practical', mark__gte=65).count()
    )
    formal_total_passed = formal_male_passed + formal_female_passed
    
    category_stats['formal'] = {
        'total': formal_total,
        'male': formal_male,
        'female': formal_female,
        'male_passed': formal_male_passed,
        'female_passed': formal_female_passed,
        'total_passed': formal_total_passed,
        'male_pass_rate': round((formal_male_passed / formal_male * 100), 2) if formal_male > 0 else 0,
        'female_pass_rate': round((formal_female_passed / formal_female * 100), 2) if formal_female > 0 else 0,
        'pass_rate': round((formal_total_passed / formal_total * 100), 2) if formal_total > 0 else 0
    }
    
    # Workers PAS category
    workers_results = WorkersPasResult.objects.filter(assessment_series_id=series_id).select_related('candidate')
    workers_total = workers_results.count()
    workers_male_results = workers_results.filter(candidate__gender='male')
    workers_female_results = workers_results.filter(candidate__gender='female')
    
    workers_male = workers_male_results.count()
    workers_female = workers_female_results.count()
    workers_male_passed = workers_male_results.filter(mark__gte=65).count()
    workers_female_passed = workers_female_results.filter(mark__gte=65).count()
    workers_total_passed = workers_male_passed + workers_female_passed
    
    category_stats['workers_pas'] = {
        'total': workers_total,
        'male': workers_male,
        'female': workers_female,
        'male_passed': workers_male_passed,
        'female_passed': workers_female_passed,
        'total_passed': workers_total_passed,
        'male_pass_rate': round((workers_male_passed / workers_male * 100), 2) if workers_male > 0 else 0,
        'female_pass_rate': round((workers_female_passed / workers_female * 100), 2) if workers_female > 0 else 0,
        'pass_rate': round((workers_total_passed / workers_total * 100), 2) if workers_total > 0 else 0
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
    
    # By occupation - comprehensive metrics
    occupation_stats = []
    
    # Get all occupations that have results in this series
    from occupations.models import Occupation
    occupation_ids = set()
    
    # Collect occupation IDs from all result types
    for result in all_results:
        # Modular results: occupation via module
        if hasattr(result, 'module') and result.module:
            occupation_ids.add(result.module.occupation_id)
        # Formal and Workers results: occupation via candidate
        elif hasattr(result, 'candidate') and result.candidate and result.candidate.occupation:
            occupation_ids.add(result.candidate.occupation_id)
    
    # By occupation - now reorganized by sector with summaries
    from occupations.models import Sector
    occupation_stats = []
    
    # Get all sectors
    sectors = Sector.objects.all().order_by('name')
    
    for sector in sectors:
        # Get occupations in this sector that have results
        sector_occupations = Occupation.objects.filter(
            id__in=occupation_ids,
            sector=sector
        ).order_by('occ_name')
        
        if not sector_occupations.exists():
            continue
        
        # Sector-level accumulators
        sector_total = 0
        sector_male = 0
        sector_female = 0
        sector_male_passed = 0
        sector_female_passed = 0
        sector_total_passed = 0
        
        for occ in sector_occupations:
            # Get all results for this occupation
            occ_modular = ModularResult.objects.filter(
                assessment_series_id=series_id,
                module__occupation=occ
            ).select_related('candidate')
            
            occ_formal = FormalResult.objects.filter(
                assessment_series_id=series_id,
                candidate__occupation=occ
            ).select_related('candidate')
            
            occ_workers = WorkersPasResult.objects.filter(
                assessment_series_id=series_id,
                candidate__occupation=occ
            ).select_related('candidate')
            
            # Combine all results for this occupation
            occ_all_results = list(occ_modular) + list(occ_formal) + list(occ_workers)
            
            if len(occ_all_results) == 0:
                continue
            
            # Calculate statistics
            total = len(occ_all_results)
            male_results = [r for r in occ_all_results if r.candidate.gender == 'male']
            female_results = [r for r in occ_all_results if r.candidate.gender == 'female']
            
            male_count = len(male_results)
            female_count = len(female_results)
            
            # Count passing (based on result type)
            male_passed = sum(1 for r in male_results if (
                (isinstance(r, ModularResult) and r.mark >= 65) or
                (isinstance(r, FormalResult) and ((r.type == 'theory' and r.mark >= 50) or (r.type == 'practical' and r.mark >= 65))) or
                (isinstance(r, WorkersPasResult) and r.mark >= 65)
            ))
            
            female_passed = sum(1 for r in female_results if (
                (isinstance(r, ModularResult) and r.mark >= 65) or
                (isinstance(r, FormalResult) and ((r.type == 'theory' and r.mark >= 50) or (r.type == 'practical' and r.mark >= 65))) or
                (isinstance(r, WorkersPasResult) and r.mark >= 65)
            ))
            
            total_passed = male_passed + female_passed
            
            # Add to sector totals
            sector_total += total
            sector_male += male_count
            sector_female += female_count
            sector_male_passed += male_passed
            sector_female_passed += female_passed
            sector_total_passed += total_passed
            
            occupation_stats.append({
                'occupation_name': occ.occ_name,
                'occupation_code': occ.occ_code,
                'sector_name': sector.name,
                'total': total,
                'male': male_count,
                'female': female_count,
                'male_passed': male_passed,
                'female_passed': female_passed,
                'total_passed': total_passed,
                'male_pass_rate': round((male_passed / male_count * 100), 2) if male_count > 0 else 0,
                'female_pass_rate': round((female_passed / female_count * 100), 2) if female_count > 0 else 0,
                'pass_rate': round((total_passed / total * 100), 2) if total > 0 else 0,
                'is_sector_summary': False
            })
        
        # Add sector summary row
        if sector_total > 0:
            occupation_stats.append({
                'occupation_name': f'{sector.name} - TOTAL',
                'occupation_code': '',
                'sector_name': sector.name,
                'total': sector_total,
                'male': sector_male,
                'female': sector_female,
                'male_passed': sector_male_passed,
                'female_passed': sector_female_passed,
                'total_passed': sector_total_passed,
                'male_pass_rate': round((sector_male_passed / sector_male * 100), 2) if sector_male > 0 else 0,
                'female_pass_rate': round((sector_female_passed / sector_female * 100), 2) if sector_female > 0 else 0,
                'pass_rate': round((sector_total_passed / sector_total * 100), 2) if sector_total > 0 else 0,
                'is_sector_summary': True
            })
    
    # By sector - NEW comprehensive metrics
    sector_stats = []
    
    sectors = Sector.objects.all()
    
    for sector in sectors:
        # Get all results for occupations in this sector
        sector_occs = Occupation.objects.filter(sector=sector)
        
        sector_modular = ModularResult.objects.filter(
            assessment_series_id=series_id,
            module__occupation__in=sector_occs
        ).select_related('candidate')
        
        sector_formal = FormalResult.objects.filter(
            assessment_series_id=series_id,
            candidate__occupation__in=sector_occs
        ).select_related('candidate')
        
        sector_workers = WorkersPasResult.objects.filter(
            assessment_series_id=series_id,
            candidate__occupation__in=sector_occs
        ).select_related('candidate')
        
        # Combine all results for this sector
        sector_all_results = list(sector_modular) + list(sector_formal) + list(sector_workers)
        
        if len(sector_all_results) == 0:
            continue
        
        # Calculate statistics
        total = len(sector_all_results)
        male_results = [r for r in sector_all_results if r.candidate.gender == 'male']
        female_results = [r for r in sector_all_results if r.candidate.gender == 'female']
        
        male_count = len(male_results)
        female_count = len(female_results)
        
        # Count passing
        male_passed = sum(1 for r in male_results if (
            (isinstance(r, ModularResult) and r.mark >= 65) or
            (isinstance(r, FormalResult) and ((r.type == 'theory' and r.mark >= 50) or (r.type == 'practical' and r.mark >= 65))) or
            (isinstance(r, WorkersPasResult) and r.mark >= 65)
        ))
        
        female_passed = sum(1 for r in female_results if (
            (isinstance(r, ModularResult) and r.mark >= 65) or
            (isinstance(r, FormalResult) and ((r.type == 'theory' and r.mark >= 50) or (r.type == 'practical' and r.mark >= 65))) or
            (isinstance(r, WorkersPasResult) and r.mark >= 65)
        ))
        
        total_passed = male_passed + female_passed
        
        sector_stats.append({
            'sector_name': sector.name,
            'total': total,
            'male': male_count,
            'female': female_count,
            'male_passed': male_passed,
            'female_passed': female_passed,
            'total_passed': total_passed,
            'male_pass_rate': round((male_passed / male_count * 100), 2) if male_count > 0 else 0,
            'female_pass_rate': round((female_passed / female_count * 100), 2) if female_count > 0 else 0,
            'pass_rate': round((total_passed / total * 100), 2) if total > 0 else 0
        })
    
    # Centers by Sector - count unique centers and branches per sector
    from assessment_centers.models import AssessmentCenter, CenterBranch
    centers_by_sector = []
    
    # Track unique centers and branches across the entire series
    series_unique_centers = set()
    series_unique_branches = set()
    
    for sector in Sector.objects.all().order_by('name'):
        # Filter results for this sector - matching Excel export logic to ensure consistency
        sector_results = [r for r in all_results if 
                         (hasattr(r, 'module') and r.module and r.module.occupation.sector == sector) or
                         (hasattr(r, 'candidate') and r.candidate.occupation and r.candidate.occupation.sector == sector)]
        
        # Get unique centers (parents) and branches for this sector
        sector_centers = set()
        sector_branches = set()
        
        for r in sector_results:
            cand = r.candidate
            
            # Use assessment_center_id (Parent) for Centers count
            if cand.assessment_center_id:
                sector_centers.add(cand.assessment_center_id)
                series_unique_centers.add(cand.assessment_center_id)
            
            # Use assessment_center_branch_id for Branches count
            if cand.assessment_center_branch_id:
                sector_branches.add(cand.assessment_center_branch_id)
                series_unique_branches.add(cand.assessment_center_branch_id)
        
        if len(sector_centers) > 0 or len(sector_branches) > 0:
            centers_by_sector.append({
                'sector_name': sector.name,
                'centers_count': len(sector_centers),
                'branches_count': len(sector_branches)
            })
            
    # Add total summary row
    centers_by_sector_summary = {
        'total_unique_centers': len(series_unique_centers),
        'total_unique_branches': len(series_unique_branches)
    }
    
    return Response({
        'series': {
            'id': series.id,
            'name': series.name,
            'start_date': series.start_date,
            'end_date': series.end_date
        },
        'overview': overview,
        'centers_by_sector': centers_by_sector,
        'centers_by_sector_summary': centers_by_sector_summary,
        'by_category': category_stats,
        'grade_distribution': grade_dist,
        'by_occupation': occupation_stats,
        'by_sector': sector_stats
    })


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


