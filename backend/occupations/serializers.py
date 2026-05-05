from rest_framework import serializers
from .models import Sector, Occupation, OccupationLevel, OccupationModule, OccupationPaper, ModuleLWA


class SectorSerializer(serializers.ModelSerializer):
    occupations_count = serializers.IntegerField(source='get_occupations_count', read_only=True)
    
    class Meta:
        model = Sector
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class OccupationLevelSerializer(serializers.ModelSerializer):
    occupation_code = serializers.CharField(source='occupation.occ_code', read_only=True)
    occupation_name = serializers.CharField(source='occupation.occ_name', read_only=True)
    structure_type_display = serializers.CharField(source='get_structure_type_display', read_only=True)
    
    class Meta:
        model = OccupationLevel
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'occupation']


class OccupationLevelCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating levels"""
    
    class Meta:
        model = OccupationLevel
        fields = ['occupation', 'level_name', 'structure_type', 'formal_fee', 
                  'workers_pas_base_fee', 'workers_pas_per_module_fee', 
                  'modular_fee_single_module', 'modular_fee_double_module', 
                  'award', 'contact_hours',
                  'level_description', 'competence_description',
                  'is_active']
    
    def validate(self, data):
        """Validate level name is unique for the occupation"""
        occupation = data.get('occupation')
        level_name = data.get('level_name')
        
        if OccupationLevel.objects.filter(occupation=occupation, level_name=level_name).exists():
            raise serializers.ValidationError({
                'level_name': f"A level with name '{level_name}' already exists for this occupation."
            })
        return data


class OccupationSerializer(serializers.ModelSerializer):
    occ_category_display = serializers.CharField(source='get_occ_category_display', read_only=True)
    sector_name = serializers.CharField(source='sector.name', read_only=True)
    levels_count = serializers.IntegerField(source='get_levels_count', read_only=True)
    levels = OccupationLevelSerializer(many=True, read_only=True)
    is_formal_category = serializers.BooleanField(source='is_formal', read_only=True)
    is_workers_pas_category = serializers.BooleanField(source='is_workers_pas', read_only=True)
    
    class Meta:
        model = Occupation
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class OccupationCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating occupations"""

    class Meta:
        model = Occupation
        fields = ['occ_code', 'occ_name', 'occ_category', 'wp_code',
                  'wp_occ_code', 'award_modular', 'sector', 'has_modular',
                  'cover_color', 'is_active']

    def validate_cover_color(self, value):
        """Ensure cover_color is a 7-character hex string like #RRGGBB."""
        if value in (None, ''):
            return '#7d7d7d'
        import re as _re
        if not _re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
            raise serializers.ValidationError(
                "Must be a 7-character hex colour, e.g. #7d7d7d."
            )
        return value.lower()

    def validate_occ_code(self, value):
        """Ensure occupation code is unique"""
        qs = Occupation.objects.filter(occ_code=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("An occupation with this code already exists.")
        return value

    def validate_wp_occ_code(self, value):
        """Ensure the numeric occupation code is unique across occupations."""
        if value is None:
            return value
        qs = Occupation.objects.filter(wp_occ_code=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "This Worker's PAS Occupation Number is already used by another occupation."
            )
        return value

    def validate(self, data):
        """Validate has_modular is only set for formal occupations and wp_code/wp_occ_code on WP"""
        if data.get('has_modular') and data.get('occ_category') != 'formal':
            raise serializers.ValidationError({
                'has_modular': "Modular registration is only available for Formal occupations."
            })
        if data.get('occ_category') == 'workers_pas':
            if not data.get('wp_code'):
                raise serializers.ValidationError({
                    'wp_code': "Worker's PAS Code is required for Worker's PAS occupations (e.g. BLD)."
                })
            if not data.get('wp_occ_code'):
                raise serializers.ValidationError({
                    'wp_occ_code': "Worker's PAS Occupation Number is required for "
                                   "Worker's PAS occupations (e.g. 26 for Builder)."
                })
        if data.get('wp_code'):
            data['wp_code'] = data['wp_code'].upper()
        return data


class OccupationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing occupations"""
    occ_category_display = serializers.CharField(source='get_occ_category_display', read_only=True)
    sector_name = serializers.CharField(source='sector.name', read_only=True)
    levels_count = serializers.IntegerField(source='get_levels_count', read_only=True)
    
    class Meta:
        model = Occupation
        fields = ['id', 'occ_code', 'occ_name', 'occ_category', 'occ_category_display',
                  'wp_code', 'wp_occ_code', 'award_modular', 'sector', 'sector_name',
                  'has_modular', 'levels_count', 'is_active']


class OccupationModuleSerializer(serializers.ModelSerializer):
    occupation_code = serializers.CharField(source='occupation.occ_code', read_only=True)
    occupation_name = serializers.CharField(source='occupation.occ_name', read_only=True)
    level_name = serializers.CharField(source='level.level_name', read_only=True)
    papers = serializers.SerializerMethodField()
    
    class Meta:
        model = OccupationModule
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_papers(self, obj):
        """Get papers that belong to this module (for Workers PAS)"""
        papers = obj.papers.filter(is_active=True)
        return [{
            'id': p.id,
            'paper_code': p.paper_code,
            'paper_name': p.paper_name,
            'paper_type': p.paper_type,
            'paper_type_display': p.get_paper_type_display()
        } for p in papers]


class ModuleLWASerializer(serializers.ModelSerializer):
    """Serializer for Module LWAs"""
    
    class Meta:
        model = ModuleLWA
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class OccupationModuleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating modules with validation"""
    
    class Meta:
        model = OccupationModule
        fields = ['module_code', 'module_name', 'occupation', 'level', 'credit_units',
                  'wp_description', 'wp_competence_items', 'is_active']
    
    def validate_module_code(self, value):
        """Ensure module code is unique"""
        if OccupationModule.objects.filter(module_code=value).exists():
            raise serializers.ValidationError("A module with this code already exists.")
        return value
    
    def validate(self, data):
        """Validate that level belongs to the selected occupation"""
        occupation = data.get('occupation')
        level = data.get('level')
        
        if occupation and level:
            if level.occupation != occupation:
                raise serializers.ValidationError({
                    'level': f'The selected level does not belong to {occupation.occ_name}'
                })
        return data


class OccupationPaperSerializer(serializers.ModelSerializer):
    occupation_code = serializers.CharField(source='occupation.occ_code', read_only=True)
    occupation_name = serializers.CharField(source='occupation.occ_name', read_only=True)
    level_name = serializers.CharField(source='level.level_name', read_only=True)
    module_code = serializers.CharField(source='module.module_code', read_only=True)
    module_name = serializers.CharField(source='module.module_name', read_only=True)
    paper_type_display = serializers.CharField(source='get_paper_type_display', read_only=True)
    
    class Meta:
        model = OccupationPaper
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class OccupationPaperCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating papers with validation"""
    
    class Meta:
        model = OccupationPaper
        fields = ['paper_code', 'paper_name', 'occupation', 'level', 'module', 'paper_type', 'credit_units', 'is_active']
    
    def validate_paper_code(self, value):
        """Ensure paper code is unique"""
        if OccupationPaper.objects.filter(paper_code=value).exists():
            raise serializers.ValidationError("A paper with this code already exists.")
        return value
    
    def validate(self, data):
        """Validate that level belongs to the selected occupation"""
        occupation = data.get('occupation')
        level = data.get('level')
        
        if occupation and level:
            if level.occupation != occupation:
                raise serializers.ValidationError({
                    'level': f'The selected level does not belong to {occupation.occ_name}'
                })
        return data