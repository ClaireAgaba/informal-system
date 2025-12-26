from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Staff, SupportStaff


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