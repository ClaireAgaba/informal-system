from rest_framework import serializers
from .models import User, Staff, SupportStaff
from configurations.serializers import DepartmentSerializer


class UserSerializer(serializers.ModelSerializer):
    user_type_display = serializers.CharField(source='get_user_type_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type', 
                  'user_type_display', 'phone_number', 'is_active', 'date_joined']
        read_only_fields = ['date_joined']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class StaffSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_details = DepartmentSerializer(source='department', read_only=True)
    account_status_display = serializers.CharField(source='get_account_status_display', read_only=True)
    accessible_modules = serializers.SerializerMethodField()
    is_account_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Staff
        fields = '__all__'
        read_only_fields = ['date_joined', 'last_login', 'created_at', 'updated_at']
    
    def get_accessible_modules(self, obj):
        """Return list of modules this staff member can access"""
        return obj.get_accessible_modules()
    
    def get_is_account_active(self, obj):
        """Return if account is active"""
        return obj.is_active()


class StaffCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating staff members"""
    
    class Meta:
        model = Staff
        fields = ['full_name', 'email', 'contact', 'department', 'account_status']
    
    def validate_email(self, value):
        """Ensure email is unique"""
        if Staff.objects.filter(email=value).exists():
            raise serializers.ValidationError("A staff member with this email already exists.")
        return value


class SupportStaffSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_details = DepartmentSerializer(source='department', read_only=True)
    account_status_display = serializers.CharField(source='get_account_status_display', read_only=True)
    accessible_modules = serializers.SerializerMethodField()
    is_account_active = serializers.SerializerMethodField()
    
    class Meta:
        model = SupportStaff
        fields = '__all__'
        read_only_fields = ['date_joined', 'last_login', 'created_at', 'updated_at']
    
    def get_accessible_modules(self, obj):
        """Return list of modules this support staff member can access"""
        return obj.get_accessible_modules()
    
    def get_is_account_active(self, obj):
        """Return if account is active"""
        return obj.is_active()


class SupportStaffCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating support staff members"""
    
    class Meta:
        model = SupportStaff
        fields = ['full_name', 'contact', 'email', 'department', 'account_status']
    
    def validate_email(self, value):
        """Ensure email is unique"""
        if SupportStaff.objects.filter(email=value).exists():
            raise serializers.ValidationError("A support staff member with this email already exists.")
        return value