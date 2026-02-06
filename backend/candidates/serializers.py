from rest_framework import serializers
from .models import Candidate, CandidateEnrollment, EnrollmentModule, EnrollmentPaper, CandidateActivity
from configurations.models import District, Village, NatureOfDisability
from assessment_centers.models import AssessmentCenter, CenterBranch
from occupations.models import Occupation, OccupationLevel, OccupationModule, OccupationPaper
from assessment_series.models import AssessmentSeries
from users.models import Staff
from results.models import FormalResult, ModularResult
from datetime import date
from utils.nationality_helper import get_nationality_from_country


class CandidateListSerializer(serializers.ModelSerializer):
    """Serializer for candidate list view with related data"""
    assessment_center = serializers.SerializerMethodField()
    occupation = serializers.SerializerMethodField()
    sector = serializers.SerializerMethodField()
    district_name = serializers.CharField(source='district.name', read_only=True)
    village_name = serializers.CharField(source='village.name', read_only=True)
    enrollments = serializers.SerializerMethodField()
    has_special_needs = serializers.SerializerMethodField()
    is_enrolled = serializers.SerializerMethodField()
    has_marks = serializers.SerializerMethodField()
    nationality_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Candidate
        fields = [
            'id', 'registration_number', 'payment_code', 'is_submitted', 'full_name', 'date_of_birth', 'gender',
            'nationality', 'candidate_country', 'nationality_display', 'is_refugee', 'refugee_number', 'contact',
            'district_name', 'village_name', 'has_disability', 'has_special_needs',
            'assessment_center', 'registration_category', 'occupation', 'sector',
            'entry_year', 'intake',
            'verification_status', 'status', 'passport_photo', 'enrollments',
            'is_enrolled', 'has_marks',
            'created_at', 'updated_at'
        ]
    
    def get_assessment_center(self, obj):
        if obj.assessment_center:
            return {
                'id': obj.assessment_center.id,
                'center_number': obj.assessment_center.center_number,
                'center_name': obj.assessment_center.center_name,
            }
        return None
    
    def get_occupation(self, obj):
        if obj.occupation:
            return {
                'id': obj.occupation.id,
                'occ_code': obj.occupation.occ_code,
                'occ_name': obj.occupation.occ_name,
            }
        return None
    
    def get_sector(self, obj):
        if obj.occupation and obj.occupation.sector:
            return {
                'id': obj.occupation.sector.id,
                'name': obj.occupation.sector.name,
            }
        return None
    
    def get_enrollments(self, obj):
        """Get list of enrollment data for statistics"""
        enrollments = obj.enrollments.filter(is_active=True)
        return [{
            'id': e.id,
            'assessment_series': e.assessment_series.id,
            'occupation': e.occupation_level.occupation.id if e.occupation_level else None
        } for e in enrollments]
    
    def get_has_special_needs(self, obj):
        """Check if candidate has special needs (disability)"""
        return obj.has_disability
    
    def get_is_enrolled(self, obj):
        """Check if candidate has any active enrollments"""
        return obj.enrollments.filter(is_active=True).exists()
    
    def get_has_marks(self, obj):
        """Check if candidate has any marks/results"""
        # Check for formal results
        has_formal_results = FormalResult.objects.filter(candidate=obj).exists()
        # Check for modular results
        has_modular_results = ModularResult.objects.filter(candidate=obj).exists()
        return has_formal_results or has_modular_results
    
    def get_nationality_display(self, obj):
        """Get nationality demonym from candidate_country field"""
        return get_nationality_from_country(obj.candidate_country) if obj.candidate_country else "Ugandan"


class CandidateDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for candidate with all related data"""
    assessment_center_detail = serializers.SerializerMethodField()
    assessment_center_branch_detail = serializers.SerializerMethodField()
    occupation_detail = serializers.SerializerMethodField()
    district_detail = serializers.SerializerMethodField()
    village_detail = serializers.SerializerMethodField()
    nature_of_disability_detail = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.fullname', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.fullname', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.fullname', read_only=True)
    age = serializers.SerializerMethodField()
    nationality_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Candidate
        fields = '__all__'
    
    def get_age(self, obj):
        return obj.get_age()
    
    def get_assessment_center_detail(self, obj):
        if obj.assessment_center:
            return {
                'id': obj.assessment_center.id,
                'center_number': obj.assessment_center.center_number,
                'center_name': obj.assessment_center.center_name,
                'assessment_category': obj.assessment_center.assessment_category,
            }
        return None
    
    def get_assessment_center_branch_detail(self, obj):
        if obj.assessment_center_branch:
            return {
                'id': obj.assessment_center_branch.id,
                'branch_name': obj.assessment_center_branch.branch_name,
                'branch_code': obj.assessment_center_branch.branch_code,
            }
        return None
    
    def get_occupation_detail(self, obj):
        if obj.occupation:
            return {
                'id': obj.occupation.id,
                'occ_code': obj.occupation.occ_code,
                'occ_name': obj.occupation.occ_name,
                'occ_category': obj.occupation.occ_category,
                'has_modular': obj.occupation.has_modular,
                'sector': {
                    'id': obj.occupation.sector.id,
                    'name': obj.occupation.sector.name,
                } if obj.occupation.sector else None
            }
        return None
    
    def get_district_detail(self, obj):
        if obj.district:
            return {
                'id': obj.district.id,
                'name': obj.district.name,
            }
        return None
    
    def get_village_detail(self, obj):
        if obj.village:
            return {
                'id': obj.village.id,
                'name': obj.village.name,
            }
        return None
    
    def get_nature_of_disability_detail(self, obj):
        if obj.nature_of_disability:
            return {
                'id': obj.nature_of_disability.id,
                'name': obj.nature_of_disability.name,
            }
        return None
    
    def get_nationality_display(self, obj):
        """Get nationality demonym from candidate_country field"""
        return get_nationality_from_country(obj.candidate_country) if obj.candidate_country else "Ugandan"


class CandidateCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating candidates"""
    
    # Use PrimaryKeyRelatedField for foreign keys so DRF handles the conversion
    district = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(),
        required=False,
        allow_null=True
    )
    village = serializers.PrimaryKeyRelatedField(
        queryset=Village.objects.all(),
        required=False,
        allow_null=True
    )
    nature_of_disability = serializers.PrimaryKeyRelatedField(
        queryset=NatureOfDisability.objects.all(),
        required=False,
        allow_null=True
    )
    assessment_center = serializers.PrimaryKeyRelatedField(
        queryset=AssessmentCenter.objects.all(),
        required=False,
        allow_null=True
    )
    assessment_center_branch = serializers.PrimaryKeyRelatedField(
        queryset=CenterBranch.objects.all(),
        required=False,
        allow_null=True
    )
    occupation = serializers.PrimaryKeyRelatedField(
        queryset=Occupation.objects.all(),
        required=False,
        allow_null=True
    )

    # Make some fields optional for updates
    entry_year = serializers.IntegerField(required=False, allow_null=True)
    intake = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    registration_category = serializers.CharField(required=False)

    class Meta:
        model = Candidate
        fields = [
            'id',
            'full_name', 'date_of_birth', 'gender', 'nationality', 'candidate_country',
            'is_refugee', 'refugee_number', 'contact', 'district', 'village',
            'has_disability', 'nature_of_disability', 'disability_specification',
            'assessment_center', 'assessment_center_branch', 'entry_year', 'intake',
            'registration_category', 'occupation', 'preferred_assessment_language',
            'start_date', 'finish_date', 'assessment_date',
            'modular_module_count', 'modular_billing_amount',
            'passport_photo',
            'identification_document', 'qualification_document',
            'enrollment_level', 'reg_number', 'status', 'block_portal_results',
            'transcript_serial_number',
        ]

    def validate_intake(self, value):
        if value in (None, ''):
            return None
        allowed = {'M', 'J', 'S', 'D', 'A'}
        if value not in allowed:
            raise serializers.ValidationError('Invalid assessment intake. Allowed values are M, J, S, D.')
        return value

    def validate_date_of_birth(self, value):
        if value in (None, ''):
            return value

        today = date.today()

        if value > today:
            raise serializers.ValidationError('Date of birth cannot be in the future.')

        def shift_years(d, years):
            try:
                return d.replace(year=d.year - years)
            except ValueError:
                return d.replace(year=d.year - years, month=2, day=28)

        min_dob = shift_years(today, 100)
        max_dob = shift_years(today, 12)

        if value < min_dob:
            raise serializers.ValidationError('Candidate cannot be older than 100 years.')
        if value > max_dob:
            raise serializers.ValidationError('Candidate must be at least 12 years old.')

        return value

    def validate(self, data):
        """Convert empty strings to None for foreign keys"""
        fk_fields = ['district', 'village', 'nature_of_disability', 
                     'assessment_center', 'assessment_center_branch', 'occupation']

        for field in fk_fields:
            if field in data and (data[field] == '' or data[field] == 'None'):
                data[field] = None

        assessment_center = data.get('assessment_center', getattr(self.instance, 'assessment_center', None))
        assessment_center_branch = data.get(
            'assessment_center_branch',
            getattr(self.instance, 'assessment_center_branch', None)
        )
        if assessment_center_branch and assessment_center:
            if assessment_center_branch.assessment_center_id != assessment_center.id:
                raise serializers.ValidationError({
                    'assessment_center_branch': 'Selected branch does not belong to the selected assessment center'
                })

        return data

    def create(self, validated_data):
        # Auto-generate registration number
        candidate = Candidate(**validated_data)
        if not candidate.registration_number:
            reg_number = candidate.generate_registration_number()
            if reg_number:
                candidate.registration_number = reg_number
        candidate.save()
        return candidate


class CandidateActivitySerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()
    actor_user_type = serializers.SerializerMethodField()
    details = serializers.SerializerMethodField()

    class Meta:
        model = CandidateActivity
        fields = [
            'id',
            'actor_name',
            'actor_user_type',
            'action',
            'description',
            'details',
            'created_at',
        ]

    def get_actor_name(self, obj):
        if not obj.actor:
            return None
        if hasattr(obj.actor, 'get_full_name'):
            name = obj.actor.get_full_name()
            return name if name else obj.actor.username
        return getattr(obj.actor, 'username', None)

    def get_actor_user_type(self, obj):
        return getattr(obj.actor, 'user_type', None) if obj.actor else None

    def get_details(self, obj):
        details = obj.details
        if details is None:
            return None
        if isinstance(details, dict):
            filtered = {}
            for k, v in details.items():
                if k == 'id' or k.endswith('_id') or k.endswith('_ids'):
                    continue
                filtered[k] = v
            return filtered
        if isinstance(details, list):
            return details
        return details


class EnrollmentModuleSerializer(serializers.ModelSerializer):
    module_code = serializers.CharField(source='module.module_code', read_only=True)
    module_name = serializers.CharField(source='module.module_name', read_only=True)
    
    class Meta:
        model = EnrollmentModule
        fields = ['id', 'module', 'module_code', 'module_name']


class EnrollmentPaperSerializer(serializers.ModelSerializer):
    paper_code = serializers.CharField(source='paper.paper_code', read_only=True)
    paper_name = serializers.CharField(source='paper.paper_name', read_only=True)
    paper_type = serializers.CharField(source='paper.paper_type', read_only=True)
    level_name = serializers.CharField(source='paper.level.level_name', read_only=True)
    module_code = serializers.CharField(source='paper.module.module_code', read_only=True)
    module_name = serializers.CharField(source='paper.module.module_name', read_only=True)
    
    class Meta:
        model = EnrollmentPaper
        fields = [
            'id', 'paper', 'paper_code', 'paper_name', 'paper_type',
            'level_name', 'module_code', 'module_name'
        ]


class CandidateEnrollmentSerializer(serializers.ModelSerializer):
    assessment_series_name = serializers.CharField(source='assessment_series.name', read_only=True)
    level_name = serializers.SerializerMethodField()
    level_id = serializers.IntegerField(source='occupation_level.id', read_only=True)
    occupation_name = serializers.SerializerMethodField()
    structure_type = serializers.CharField(source='occupation_level.structure_type', read_only=True)
    modules = EnrollmentModuleSerializer(many=True, read_only=True)
    papers = EnrollmentPaperSerializer(many=True, read_only=True)
    
    def get_level_name(self, obj):
        """Get level name - for Worker's PAS, get from enrolled papers"""
        if obj.occupation_level:
            return obj.occupation_level.level_name
        
        # For Worker's PAS, get unique levels from enrolled papers
        if obj.papers.exists():
            levels = set()
            for enrollment_paper in obj.papers.all():
                if enrollment_paper.paper and enrollment_paper.paper.level:
                    levels.add(enrollment_paper.paper.level.level_name)
            return ', '.join(sorted(levels)) if levels else None
        
        return None
    
    def get_occupation_name(self, obj):
        """Get occupation name"""
        if obj.occupation_level:
            return obj.occupation_level.occupation.occ_name
        
        # For Worker's PAS, get from first enrolled paper
        if obj.papers.exists():
            first_paper = obj.papers.first()
            if first_paper and first_paper.paper:
                return first_paper.paper.occupation.occ_name
        
        return None
    
    class Meta:
        model = CandidateEnrollment
        fields = [
            'id', 'candidate', 'assessment_series', 'assessment_series_name',
            'occupation_level', 'level_id', 'level_name', 'occupation_name', 'structure_type',
            'total_amount', 'modules', 'papers', 'is_active',
            'enrolled_at', 'updated_at'
        ]
        read_only_fields = ['enrolled_at', 'updated_at']


class EnrollmentListSerializer(serializers.ModelSerializer):
    """Serializer for listing all enrollments with candidate details"""
    registration_number = serializers.CharField(source='candidate.registration_number', read_only=True)
    candidate_name = serializers.CharField(source='candidate.full_name', read_only=True)
    candidate_id = serializers.IntegerField(source='candidate.id', read_only=True)
    registration_category = serializers.CharField(source='candidate.registration_category', read_only=True)
    occupation_name = serializers.SerializerMethodField()
    occupation_code = serializers.SerializerMethodField()
    assessment_series_name = serializers.CharField(source='assessment_series.name', read_only=True)
    assessment_series_id = serializers.IntegerField(source='assessment_series.id', read_only=True)
    level_name = serializers.SerializerMethodField()
    modules_display = serializers.SerializerMethodField()
    center_name = serializers.CharField(source='candidate.assessment_center.center_name', read_only=True)
    center_number = serializers.CharField(source='candidate.assessment_center.center_number', read_only=True)
    
    def get_occupation_name(self, obj):
        if obj.occupation_level:
            return obj.occupation_level.occupation.occ_name
        if obj.modules.exists():
            first_module = obj.modules.first()
            if first_module and first_module.module:
                return first_module.module.occupation.occ_name
        if obj.papers.exists():
            first_paper = obj.papers.first()
            if first_paper and first_paper.paper:
                return first_paper.paper.occupation.occ_name
        return obj.candidate.occupation.occ_name if obj.candidate.occupation else None
    
    def get_occupation_code(self, obj):
        if obj.occupation_level:
            return obj.occupation_level.occupation.occ_code
        if obj.modules.exists():
            first_module = obj.modules.first()
            if first_module and first_module.module:
                return first_module.module.occupation.occ_code
        if obj.papers.exists():
            first_paper = obj.papers.first()
            if first_paper and first_paper.paper:
                return first_paper.paper.occupation.occ_code
        return obj.candidate.occupation.occ_code if obj.candidate.occupation else None
    
    def get_level_name(self, obj):
        """Get level name(s) - for formal candidates"""
        if obj.occupation_level:
            return obj.occupation_level.level_name
        # For Worker's PAS, get unique levels from enrolled papers
        if obj.papers.exists():
            levels = set()
            for enrollment_paper in obj.papers.all():
                if enrollment_paper.paper and enrollment_paper.paper.level:
                    levels.add(enrollment_paper.paper.level.level_name)
            return ', '.join(sorted(levels)) if levels else None
        return None
    
    def get_modules_display(self, obj):
        """Get modules for modular/workers_pas candidates"""
        if obj.modules.exists():
            return ', '.join([m.module.module_code for m in obj.modules.all()])
        return None
    
    class Meta:
        model = CandidateEnrollment
        fields = [
            'id', 'candidate_id', 'registration_number', 'candidate_name',
            'registration_category', 'occupation_code', 'occupation_name',
            'assessment_series_id', 'assessment_series_name',
            'level_name', 'modules_display', 'center_name', 'center_number',
            'total_amount', 'is_active', 'enrolled_at'
        ]


class EnrollCandidateSerializer(serializers.Serializer):
    """Serializer for enrolling a candidate"""
    assessment_series = serializers.IntegerField()
    occupation_level = serializers.IntegerField(required=False, allow_null=True)
    modules = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    papers = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    
    def validate(self, data):
        # Validate assessment series exists
        try:
            assessment_series = AssessmentSeries.objects.get(id=data['assessment_series'])
        except AssessmentSeries.DoesNotExist:
            raise serializers.ValidationError({'assessment_series': 'Invalid assessment series'})
        
        # Get candidate from context
        candidate = self.context.get('candidate')
        if not candidate:
            raise serializers.ValidationError('Candidate not found in context')
        
        # Validate based on registration category
        reg_category = candidate.registration_category
        
        # For formal and modular, occupation_level is required
        occupation_level = None
        if reg_category in ['formal', 'modular']:
            if not data.get('occupation_level'):
                raise serializers.ValidationError({'occupation_level': 'Occupation level is required'})
            try:
                occupation_level = OccupationLevel.objects.get(id=data['occupation_level'])
            except OccupationLevel.DoesNotExist:
                raise serializers.ValidationError({'occupation_level': 'Invalid occupation level'})
        
        if reg_category == 'formal':
            # Formal: no modules or papers needed
            if data.get('modules') or data.get('papers'):
                raise serializers.ValidationError('Formal registration does not require modules or papers')
        
        elif reg_category == 'modular':
            # Modular: must select 1-2 modules from level 1
            modules = data.get('modules', [])
            if not modules or len(modules) < 1 or len(modules) > 2:
                raise serializers.ValidationError({'modules': 'Modular registration requires 1 or 2 modules'})
            
            # Validate modules belong to level 1 of the occupation
            level_1 = occupation_level.occupation.levels.filter(level_name__icontains='level 1').first()
            if not level_1:
                raise serializers.ValidationError('Level 1 not found for this occupation')
            
            valid_modules = OccupationModule.objects.filter(
                id__in=modules,
                level=level_1,
                occupation=occupation_level.occupation
            )
            if valid_modules.count() != len(modules):
                raise serializers.ValidationError({'modules': 'Invalid modules selected'})
        
        elif reg_category == 'workers_pas':
            # Workers PAS: must select 2-4 papers from any level
            papers = data.get('papers', [])
            
            if not papers:
                raise serializers.ValidationError({'papers': "Worker's PAS registration requires papers"})
            
            if len(papers) < 2:
                raise serializers.ValidationError({'papers': 'Minimum 2 papers required'})
            
            if len(papers) > 4:
                raise serializers.ValidationError({'papers': 'Maximum 4 papers allowed'})
            
            # Validate papers belong to the candidate's occupation
            valid_papers = OccupationPaper.objects.filter(
                id__in=papers,
                occupation=candidate.occupation
            )
            if valid_papers.count() != len(papers):
                raise serializers.ValidationError({'papers': 'Invalid papers selected'})
            
            # For Workers PAS, we don't use occupation_level
            # Set it to None to indicate it's not applicable
            occupation_level = None
        
        data['assessment_series_obj'] = assessment_series
        data['occupation_level_obj'] = occupation_level
        return data


class BulkEnrollSerializer(serializers.Serializer):
    """Serializer for bulk enrolling multiple candidates"""
    candidate_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    assessment_series = serializers.IntegerField()
    occupation_level = serializers.IntegerField(required=False, allow_null=True)
    modules = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    papers = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    
    def validate(self, data):
        # Validate assessment series exists
        try:
            assessment_series = AssessmentSeries.objects.get(id=data['assessment_series'])
        except AssessmentSeries.DoesNotExist:
            raise serializers.ValidationError({'assessment_series': 'Invalid assessment series'})
        
        # Validate occupation level exists (optional for workers_pas)
        occupation_level = None
        if data.get('occupation_level'):
            try:
                occupation_level = OccupationLevel.objects.get(id=data['occupation_level'])
            except OccupationLevel.DoesNotExist:
                raise serializers.ValidationError({'occupation_level': 'Invalid occupation level'})
        
        # Validate modules/papers if provided
        modules = data.get('modules', [])
        papers = data.get('papers', [])
        
        valid_modules = []
        if modules and occupation_level:
            valid_modules = list(OccupationModule.objects.filter(
                id__in=modules,
                level=occupation_level,
                occupation=occupation_level.occupation
            ))
            if len(valid_modules) != len(modules):
                raise serializers.ValidationError({'modules': 'Invalid modules selected for this level'})
        
        valid_papers = []
        if papers:
            # For workers_pas, papers can be from any level
            valid_papers = list(OccupationPaper.objects.filter(id__in=papers))
            if len(valid_papers) != len(papers):
                raise serializers.ValidationError({'papers': 'Invalid papers selected for this occupation'})
        
        data['assessment_series_obj'] = assessment_series
        data['occupation_level_obj'] = occupation_level
        data['modules'] = valid_modules
        data['papers'] = valid_papers
        return data
