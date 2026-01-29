from collections import defaultdict

class StatisticsAggregator:
    def __init__(self, name='', code=''):
        self.name = name
        self.code = code
        
        # Counters
        self.enrolled = {'total': 0, 'male': 0, 'female': 0}
        self.missing = {'total': 0, 'male': 0, 'female': 0}
        self.sat = {'total': 0, 'male': 0, 'female': 0}
        self.passed = {'total': 0, 'male': 0, 'female': 0}
        self.failed = {'total': 0, 'male': 0, 'female': 0}

    def update(self, gender, is_missing, is_sat, is_passed):
        """
        Update stats for a single candidate.
        gender: 'male' or 'female'
        is_missing: bool
        is_sat: bool
        is_passed: bool (only relevant if is_sat is True)
        """
        # Enrolled (everyone is enrolled)
        self.enrolled['total'] += 1
        if gender == 'male':
            self.enrolled['male'] += 1
        elif gender == 'female':
            self.enrolled['female'] += 1

        # Missing
        if is_missing:
            self.missing['total'] += 1
            if gender == 'male':
                self.missing['male'] += 1
            elif gender == 'female':
                self.missing['female'] += 1

        # Sat
        if is_sat:
            self.sat['total'] += 1
            if gender == 'male':
                self.sat['male'] += 1
            elif gender == 'female':
                self.sat['female'] += 1

            # Outcome (Passed/Failed) - only if Sat
            if is_passed:
                self.passed['total'] += 1
                if gender == 'male':
                    self.passed['male'] += 1
                elif gender == 'female':
                    self.passed['female'] += 1
            else:
                self.failed['total'] += 1
                if gender == 'male':
                    self.failed['male'] += 1
                elif gender == 'female':
                    self.failed['female'] += 1

    def get_stats(self):
        """
        Return a dictionary with all metrics calculated.
        """
        # Helper for safer division
        def rate(num, denom):
            return round((num / denom) * 100, 2) if denom > 0 else 0

        stats = {
            'name': self.name,
            'code': self.code,
            
            # Enrolled
            'enrolled': self.enrolled['total'],
            'male_enrolled': self.enrolled['male'],
            'female_enrolled': self.enrolled['female'],
            
            # Missing (Counts)
            'missing': self.missing['total'],
            'male_missing': self.missing['male'],
            'female_missing': self.missing['female'],
            
            # Sat (Counts)
            'sat': self.sat['total'],
            'male_sat': self.sat['male'],
            'female_sat': self.sat['female'],
            
            # Passed (Counts)
            'passed': self.passed['total'],
            'male_passed': self.passed['male'],
            'female_passed': self.passed['female'],
            
            # Failed (Counts)
            'failed': self.failed['total'],
            'male_failed': self.failed['male'],
            'female_failed': self.failed['female'],

            # --- RATES ---

            # Missing Rates (Denominator = Enrolled of same gender)
            'missing_rate': rate(self.missing['total'], self.enrolled['total']),
            'male_missing_rate': rate(self.missing['male'], self.enrolled['male']),
            'female_missing_rate': rate(self.missing['female'], self.enrolled['female']),

            # Sat Rates (Denominator = Enrolled of same gender)
            'sat_rate': rate(self.sat['total'], self.enrolled['total']),
            'male_sat_rate': rate(self.sat['male'], self.enrolled['male']),
            'female_sat_rate': rate(self.sat['female'], self.enrolled['female']),

            # Pass Rates (Denominator = Sat of same gender) -> "fraction of candidates who sat"
            'pass_rate': rate(self.passed['total'], self.sat['total']),
            'male_pass_rate': rate(self.passed['male'], self.sat['male']),
            'female_pass_rate': rate(self.passed['female'], self.sat['female']),

            # Fail Rates (Denominator = Sat of same gender)
            'fail_rate': rate(self.failed['total'], self.sat['total']),
            'male_fail_rate': rate(self.failed['male'], self.sat['male']),
            'female_fail_rate': rate(self.failed['female'], self.sat['female']),
        }
        return stats


def calculate_series_statistics(series_id, center_ids=None):
    """
    Centralized function to calculate statistics for an assessment series.
    Returns a dictionary structure suitable for both API response and Excel export.
    """
    from candidates.models import CandidateEnrollment
    from results.models import ModularResult, FormalResult, WorkersPasResult
    from assessment_series.models import AssessmentSeries
    
    # Fetch Series
    try:
        series = AssessmentSeries.objects.get(id=series_id)
    except AssessmentSeries.DoesNotExist:
        return None

    # 1. Fetch Enrollments
    enrollments_qs = CandidateEnrollment.objects.filter(
        assessment_series_id=series_id
    ).select_related(
        'candidate', 
        'candidate__occupation', 
        'candidate__occupation__sector',
        'candidate__assessment_center',
        'candidate__assessment_center_branch'
    )
    
    # 2. Fetch Results
    modular_qs = ModularResult.objects.filter(assessment_series_id=series_id)
    formal_qs = FormalResult.objects.filter(assessment_series_id=series_id)
    workers_qs = WorkersPasResult.objects.filter(assessment_series_id=series_id)
    
    # Filter by Centers if provided
    if center_ids:
        enrollments_qs = enrollments_qs.filter(candidate__assessment_center_id__in=center_ids)
        modular_qs = modular_qs.filter(candidate__assessment_center_id__in=center_ids)
        formal_qs = formal_qs.filter(candidate__assessment_center_id__in=center_ids)
        workers_qs = workers_qs.filter(candidate__assessment_center_id__in=center_ids)
        
    # 3. Map Results by Candidate ID
    candidate_results = defaultdict(list)
    all_results_flat = list(modular_qs) + list(formal_qs) + list(workers_qs)
    for r in all_results_flat:
        if r.candidate_id:
            candidate_results[r.candidate_id].append(r)

    # Helper: Check if result is passing
    def is_result_passed(result):
        if isinstance(result, ModularResult):
            return result.mark >= 65
        elif isinstance(result, FormalResult):
            if result.type == 'theory':
                return result.mark >= 50
            return result.mark >= 65  # practical
        elif isinstance(result, WorkersPasResult):
            return result.mark >= 65
        return False

    # 4. Initialize Aggregators
    overview_agg = StatisticsAggregator('Overview')
    
    category_aggs = {
        'modular': StatisticsAggregator('Modular'),
        'formal': StatisticsAggregator('Formal'),
        'workers_pas': StatisticsAggregator("Worker's PAS")
    }
    
    sector_aggs = defaultdict(lambda: StatisticsAggregator(''))
    occupation_aggs = defaultdict(lambda: StatisticsAggregator(''))
    
    # Auxiliary Meta for sorting/naming
    sector_meta = {} # name -> id
    occupation_meta = {} # id -> {name, code, sector_name}
    
    # Centers tracking
    sector_centers_map = defaultdict(set)
    sector_branches_map = defaultdict(set)
    all_unique_centers = set()
    all_unique_branches = set()

    # 5. Iteration & Aggregation
    for enrollment in enrollments_qs:
        cand = enrollment.candidate
        gender = cand.gender
        
        # Determine Status
        results = candidate_results.get(cand.id, [])
        is_sat = len(results) > 0
        is_missing = not is_sat
        
        # Default pass status
        is_passed = False
        if is_sat:
            # Candidate passes if ALL their results are passing 
            # (assuming they must take all required papers, but simplified here to "all taken results passed")
            is_passed = all(is_result_passed(r) for r in results)
            
        # Update General Overview
        overview_agg.update(gender, is_missing, is_sat, is_passed)
        
        # Update Category Stats
        cat_key = cand.registration_category or 'other'
        if cat_key not in category_aggs:
            # Dynamically create if unseen category (covers 'other' or unusual values)
            category_aggs[cat_key] = StatisticsAggregator(cat_key.title())
        
        category_aggs[cat_key].update(gender, is_missing, is_sat, is_passed)
            
        # Update Occupation & Sector Stats
        if cand.occupation:
            occ = cand.occupation
            sector = occ.sector
            occ_id = occ.id
            occ_name = occ.occ_name
            occ_code = occ.occ_code
        else:
            # Handle missing occupation (Uncategorized)
            occ_id = 'uncategorized'
            sector = None
            occ_name = 'Uncategorized'
            occ_code = 'N/A'

        sector_name = sector.name if sector else 'Uncategorized'
        
        # --- Meta Data ---
        if occ_id not in occupation_meta:
            occupation_meta[occ_id] = {
                'name': occ_name,
                'code': occ_code,
                'sector_name': sector_name
            }
        
        # Update Occupation Aggregator
        if  occupation_aggs[occ_id].name == '':
             # Update aggregator with name/code if not set
             occupation_aggs[occ_id].name = occ_name
             occupation_aggs[occ_id].code = occ_code
        
        occupation_aggs[occ_id].update(gender, is_missing, is_sat, is_passed)
        
        # Update Sector Aggregator
        if sector_name not in sector_meta:
            # Use '0' or similar for ID if Uncategorized, or just skip ID usage for meta map
            sector_meta[sector_name] = sector.id if sector else 0
         
        if sector_aggs[sector_name].name == '':
             sector_aggs[sector_name].name = sector_name
         
        sector_aggs[sector_name].update(gender, is_missing, is_sat, is_passed)
         
        # Track centers for this sector
        if cand.assessment_center:
             sector_centers_map[sector_name].add(cand.assessment_center.id)
             all_unique_centers.add(cand.assessment_center.id)
        if cand.assessment_center_branch:
             sector_branches_map[sector_name].add(cand.assessment_center_branch.id)
             all_unique_branches.add(cand.assessment_center_branch.id)

    # 6. Formatting Output
    
    # Overview
    overview_stats = overview_agg.get_stats()
    
    # Category Stats
    # Category Stats
    # Convert to list and add Total
    category_stats_list = [v.get_stats() for k, v in category_aggs.items()]
    category_stats_list.sort(key=lambda x: x['name'])
    
    # Add Grand Total Row for Categories
    cat_total = overview_agg.get_stats()
    cat_total['name'] = 'Total'
    category_stats_list.append(cat_total)
    
    # Sector Stats List (Sorted by Name)
    sector_stats_list = [agg.get_stats() for agg in sector_aggs.values()]
    sector_stats_list.sort(key=lambda x: x['name'])
    
    # Add Grand Total Row for Sectors
    sec_total = overview_agg.get_stats()
    sec_total['name'] = 'Total'
    sector_stats_list.append(sec_total)
    
    # Occupation Stats List (Grouped by Sector)
    occupation_stats_list = []
    sorted_sector_names = sorted(sector_centers_map.keys()) # Operations imply we use stored keys or meta
    # Better to use sector_aggs keys for comprehensive coverage
    sorted_sector_names = sorted(sector_aggs.keys())

    for sec_name in sorted_sector_names:
        # Find occupations in this sector
        sec_occs = [oid for oid, meta in occupation_meta.items() if meta['sector_name'] == sec_name]
        sec_occs.sort(key=lambda oid: occupation_meta[oid]['name'])
        
        for oid in sec_occs:
            stats = occupation_aggs[oid].get_stats()
            # Inject sector name for display grouping
            stats['sector_name'] = sec_name
            stats['occupation_name'] = stats['name']
            stats['occupation_code'] = stats['code']
            stats['is_sector_summary'] = False
            occupation_stats_list.append(stats)
            
        # Add Sector Summary
        sec_summary = sector_aggs[sec_name].get_stats()
        sec_summary['occupation_name'] = f"{sec_name} - TOTAL"
        sec_summary['occupation_code'] = ''
        sec_summary['sector_name'] = sec_name
        sec_summary['is_sector_summary'] = True
        sec_summary['is_sector_summary'] = True
        occupation_stats_list.append(sec_summary)
        
    # Add Grand Total Row for Occupations
    occ_total = overview_agg.get_stats()
    occ_total['occupation_name'] = 'GRAND TOTAL'
    occ_total['occupation_code'] = ''
    occ_total['sector_name'] = ''
    occ_total['is_sector_summary'] = True # Use summary styling
    occupation_stats_list.append(occ_total)
        
    # Centers by Sector
    centers_by_sector = []
    for sec_name in sorted(sector_centers_map.keys()):
        centers_by_sector.append({
            'name': sec_name,
            'centers_count': len(sector_centers_map[sec_name]),
            'branch_count': len(sector_branches_map[sec_name])
        })
        
    centers_by_sector_summary = {
        'total_centers': len(all_unique_centers),
        'total_branches': len(all_unique_branches)
    }

    # Grade Distribution
    grade_dist = defaultdict(lambda: {'total': 0, 'male': 0, 'female': 0})
    for r in all_results_flat:
        if r.grade:
            grade_dist[r.grade]['total'] += 1
            if r.candidate.gender == 'male':
                grade_dist[r.grade]['male'] += 1
            elif r.candidate.gender == 'female':
                grade_dist[r.grade]['female'] += 1

    return {
        'overview': overview_stats,
        'overview': overview_stats,
        'category_stats': category_stats_list, # Now a List with Total
        'sector_stats': sector_stats_list,
        'occupation_stats': occupation_stats_list,
        'centers_by_sector': centers_by_sector,
        'centers_by_sector_summary': centers_by_sector_summary,
        'grade_distribution': dict(grade_dist),
        'series': {
            'name': series.name,
            'start_date': series.start_date,
            'end_date': series.end_date
        }
    }
