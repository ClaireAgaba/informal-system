from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Staff, SupportStaff, CenterRepresentative


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'user_type', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['user_type', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'email')}),
    )


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'contact', 'department', 'account_status', 'date_joined']
    list_filter = ['account_status', 'department', 'date_joined']
    search_fields = ['full_name', 'email', 'contact']
    readonly_fields = ['date_joined', 'created_at', 'updated_at', 'last_login']
    autocomplete_fields = ['department']
    
    fieldsets = (
        ('Staff Information', {
            'fields': ('full_name', 'email', 'contact')
        }),
        ('Department Access', {
            'fields': ('department', 'account_status'),
            'description': 'Select the department this staff member will belong to'
        }),
        ('System Info', {
            'fields': ('user', 'date_joined', 'last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('department', 'user')


@admin.register(SupportStaff)
class SupportStaffAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'contact', 'department', 'account_status', 'date_joined']
    list_filter = ['account_status', 'department', 'date_joined']
    search_fields = ['full_name', 'email', 'contact']
    readonly_fields = ['date_joined', 'created_at', 'updated_at', 'last_login']
    autocomplete_fields = ['department']
    
    fieldsets = (
        ('Support Staff Information', {
            'fields': ('full_name', 'contact', 'email')
        }),
        ('Department Access', {
            'fields': ('department', 'account_status'),
            'description': 'Select the department this support staff member will belong to'
        }),
        ('System Info', {
            'fields': ('user', 'date_joined', 'last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('department', 'user')


@admin.register(CenterRepresentative)
class CenterRepresentativeAdmin(admin.ModelAdmin):
    list_display = ['fullname', 'email', 'contact', 'assessment_center', 'assessment_center_branch', 'account_status', 'date_joined']
    list_filter = ['account_status', 'assessment_center', 'date_joined']
    search_fields = ['fullname', 'email', 'contact', 'assessment_center__center_name']
    readonly_fields = ['email', 'date_joined', 'created_at', 'updated_at', 'last_login', 'created_by']
    autocomplete_fields = ['assessment_center', 'assessment_center_branch']
    
    fieldsets = (
        ('Representative Information', {
            'fields': ('fullname', 'contact', 'email'),
            'description': 'Email is auto-generated based on center number (e.g., uvt700@uvtab.go.ug)'
        }),
        ('Center Assignment', {
            'fields': ('assessment_center', 'assessment_center_branch', 'account_status'),
            'description': 'Select the assessment center this representative will manage'
        }),
        ('System Info', {
            'fields': ('user', 'created_by', 'date_joined', 'last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assessment_center', 'assessment_center_branch', 'user', 'created_by')
    
    def save_model(self, request, obj, form, change):
        """Set created_by on creation"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)