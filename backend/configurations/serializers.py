from rest_framework import serializers
from .models import Region, District, Village, NatureOfDisability, Department, ReprintReason


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class DistrictSerializer(serializers.ModelSerializer):
    region_display = serializers.CharField(source='get_region_display', read_only=True)
    
    class Meta:
        model = District
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class VillageSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)
    district_region = serializers.CharField(source='district.region', read_only=True)
    
    class Meta:
        model = Village
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class NatureOfDisabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = NatureOfDisability
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class DepartmentSerializer(serializers.ModelSerializer):
    module_names = serializers.SerializerMethodField()
    modules_count = serializers.SerializerMethodField()
    available_modules = serializers.SerializerMethodField()
    
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_module_names(self, obj):
        """Return human-readable names of accessible modules"""
        return obj.get_module_names()
    
    def get_modules_count(self, obj):
        """Return count of accessible modules"""
        return len(obj.module_rights)
    
    def get_available_modules(self, obj):
        """Return all available modules for selection"""
        return [{'value': app[0], 'label': app[1]} for app in Department.APP_CHOICES]


class ReprintReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReprintReason
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

