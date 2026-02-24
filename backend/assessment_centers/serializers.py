from rest_framework import serializers
from .models import AssessmentCenter, CenterBranch, CenterRepresentativePerson
from configurations.serializers import DistrictSerializer, VillageSerializer


class CenterBranchSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)
    village_name = serializers.CharField(source='village.name', read_only=True)
    branch_name = serializers.CharField(read_only=True)
    full_location = serializers.CharField(source='get_full_location', read_only=True)
    center_name = serializers.CharField(source='assessment_center.center_name', read_only=True)
    center_number = serializers.CharField(source='assessment_center.center_number', read_only=True)
    candidates_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CenterBranch
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_candidates_count(self, obj):
        from candidates.models import Candidate
        return Candidate.objects.filter(assessment_center_branch=obj).count()


class CenterBranchCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating branches"""
    
    class Meta:
        model = CenterBranch
        fields = ['assessment_center', 'branch_code', 'district', 'village', 'is_active']
    
    def validate_branch_code(self, value):
        """Ensure branch code is unique"""
        if CenterBranch.objects.filter(branch_code=value).exists():
            raise serializers.ValidationError("A branch with this code already exists.")
        return value


class AssessmentCenterSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)
    village_name = serializers.CharField(source='village.name', read_only=True)
    assessment_category_display = serializers.CharField(source='get_assessment_category_display', read_only=True)
    full_location = serializers.CharField(source='get_full_location', read_only=True)
    branches_count = serializers.IntegerField(source='get_branches_count', read_only=True)
    branches = CenterBranchSerializer(many=True, read_only=True)
    
    class Meta:
        model = AssessmentCenter
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AssessmentCenterCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating assessment centers"""
    
    class Meta:
        model = AssessmentCenter
        fields = ['center_number', 'center_name', 'assessment_category', 'district', 
                  'village', 'contact_1', 'contact_2', 'has_branches', 'is_active']
    
    def validate_center_number(self, value):
        """Ensure center number is unique"""
        if AssessmentCenter.objects.filter(center_number=value).exists():
            raise serializers.ValidationError("A center with this number already exists.")
        return value


class AssessmentCenterListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing centers"""
    district_name = serializers.CharField(source='district.name', read_only=True)
    village_name = serializers.CharField(source='village.name', read_only=True)
    assessment_category_display = serializers.CharField(source='get_assessment_category_display', read_only=True)
    branches_count = serializers.IntegerField(source='get_branches_count', read_only=True)
    
    class Meta:
        model = AssessmentCenter
        fields = ['id', 'center_number', 'center_name', 'assessment_category', 
                  'assessment_category_display', 'district', 'district_name', 'village', 
                  'village_name', 'contact_1', 'has_branches', 'branches_count', 'is_active']


class CenterRepresentativePersonSerializer(serializers.ModelSerializer):
    """Full serializer for center representative persons"""
    center_name = serializers.CharField(source='assessment_center.center_name', read_only=True)
    center_number = serializers.CharField(source='assessment_center.center_number', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    district_name = serializers.CharField(source='district.name', read_only=True, default='')

    class Meta:
        model = CenterRepresentativePerson
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class CenterRepresentativePersonCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating center representative persons"""

    class Meta:
        model = CenterRepresentativePerson
        fields = [
            'assessment_center', 'designation', 'name', 'phone',
            'email', 'nin', 'country', 'district', 'is_active',
        ]