from rest_framework import serializers
from .models import User, Staff, SupportStaff, CenterRepresentative
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


class CenterRepresentativeSerializer(serializers.ModelSerializer):
    """Serializer for Center Representatives"""
    center_name = serializers.CharField(source='assessment_center.center_name', read_only=True)
    center_number = serializers.CharField(source='assessment_center.center_number', read_only=True)
    branch_name = serializers.CharField(source='assessment_center_branch.branch_name', read_only=True)
    account_status_display = serializers.CharField(source='get_account_status_display', read_only=True)
    is_account_active = serializers.SerializerMethodField()
    
    class Meta:
        model = CenterRepresentative
        fields = [
            'id', 'fullname', 'contact', 'email', 'assessment_center', 'center_name', 
            'center_number', 'assessment_center_branch', 'branch_name', 'account_status',
            'account_status_display', 'is_account_active', 'date_joined', 'last_login',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['email', 'date_joined', 'last_login', 'created_at', 'updated_at']
    
    def get_is_account_active(self, obj):
        """Return if account is active"""
        return obj.is_active()


class CenterRepresentativeCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating center representatives"""
    
    class Meta:
        model = CenterRepresentative
        fields = ['fullname', 'contact', 'assessment_center', 'assessment_center_branch', 'account_status']
    
    def validate(self, data):
        """Validate center representative data"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        center = data['assessment_center']
        branch = data.get('assessment_center_branch')
        
        # Check if a representative already exists for this center/branch combo
        if branch:
            existing = CenterRepresentative.objects.filter(
                assessment_center=center,
                assessment_center_branch=branch
            ).exists()
            if existing:
                raise serializers.ValidationError(
                    f"A representative for this branch already exists."
                )
            # Generate email for branch
            branch_suffix = branch.branch_code.split('-')[-1] if branch.branch_code else ''
            email = f"{center.center_number.lower()}-{branch_suffix.lower()}@uvtab.go.ug"
        else:
            existing = CenterRepresentative.objects.filter(
                assessment_center=center,
                assessment_center_branch__isnull=True
            ).exists()
            if existing:
                raise serializers.ValidationError(
                    "A representative for this center already exists. Please specify a branch or update the existing representative."
                )
            email = f"{center.center_number.lower()}@uvtab.go.ug"
        
        # Check if user with this email already exists
        if User.objects.filter(username=email).exists():
            raise serializers.ValidationError(
                f"A user account with email {email} already exists."
            )
        
        return data
    
    def create(self, validated_data):
        """Create center representative with auto-generated email"""
        # Set created_by from request user
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)