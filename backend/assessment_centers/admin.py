from django.contrib import admin
from .models import AssessmentCenter, CenterBranch


class CenterBranchInline(admin.TabularInline):
    model = CenterBranch
    extra = 1
    fields = ['branch_code', 'district', 'village', 'is_active']
    autocomplete_fields = ['district', 'village']


@admin.register(AssessmentCenter)
class AssessmentCenterAdmin(admin.ModelAdmin):
    list_display = ['center_number', 'center_name', 'assessment_category', 'district', 'village', 'has_branches', 'get_branches_count', 'is_active', 'created_at']
    list_filter = ['assessment_category', 'has_branches', 'is_active', 'district', 'created_at']
    search_fields = ['center_number', 'center_name', 'contact_1', 'contact_2']
    readonly_fields = ['created_at', 'updated_at', 'get_branches_count', 'get_full_location']
    autocomplete_fields = ['district', 'village']
    inlines = [CenterBranchInline]
    # Enable autocomplete for this model in other admins
    
    fieldsets = (
        ('Center Information', {
            'fields': ('center_number', 'center_name', 'assessment_category')
        }),
        ('Location', {
            'fields': ('district', 'village', 'get_full_location'),
            'description': 'Select the district and village where this center is located'
        }),
        ('Contact Information', {
            'fields': ('contact_1', 'contact_2'),
            'description': 'Phone number or contact information for the center (optional)'
        }),
        ('Branches', {
            'fields': ('has_branches', 'get_branches_count'),
            'description': 'Check if this center will have multiple branches in different locations'
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('district', 'village').prefetch_related('branches')
    
    def get_branches_count(self, obj):
        """Display count of branches"""
        return obj.get_branches_count()
    get_branches_count.short_description = 'Branches Count'


@admin.register(CenterBranch)
class CenterBranchAdmin(admin.ModelAdmin):
    list_display = ['branch_code', 'get_center_name', 'get_center_number', 'district', 'village', 'is_active', 'created_at']
    list_filter = ['is_active', 'district', 'created_at']
    search_fields = ['branch_code', 'assessment_center__center_name', 'assessment_center__center_number']
    readonly_fields = ['created_at', 'updated_at', 'branch_name', 'get_full_location']
    autocomplete_fields = ['assessment_center', 'district', 'village']
    
    fieldsets = (
        ('Branch Information', {
            'fields': ('assessment_center', 'branch_name', 'branch_code'),
            'description': 'Branch name is inherited from the main center'
        }),
        ('Location', {
            'fields': ('district', 'village', 'get_full_location'),
            'description': 'Select the district and village where this branch is located'
        }),
        ('Status & Timestamps', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('assessment_center', 'district', 'village')
    
    def get_center_name(self, obj):
        """Display center name"""
        return obj.assessment_center.center_name
    get_center_name.short_description = 'Center Name'
    get_center_name.admin_order_field = 'assessment_center__center_name'
    
    def get_center_number(self, obj):
        """Display center number"""
        return obj.assessment_center.center_number
    get_center_number.short_description = 'Center Number'
    get_center_number.admin_order_field = 'assessment_center__center_number'