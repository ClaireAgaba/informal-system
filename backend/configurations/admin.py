from django.contrib import admin
from django import forms
from .models import Region, District, Village, NatureOfDisability, Department


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'name']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


class VillageInline(admin.TabularInline):
    model = Village
    extra = 1
    fields = ['name', 'is_active']


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'region', 'is_active', 'created_at']
    list_filter = ['region', 'is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [VillageInline]
    autocomplete_fields = []  # Enable autocomplete for this model


@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ['name', 'district', 'is_active', 'created_at']
    list_filter = ['district__region', 'district', 'is_active', 'created_at']
    search_fields = ['name', 'district__name']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['district']  # Enable autocomplete for district field


@admin.register(NatureOfDisability)
class NatureOfDisabilityAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


class DepartmentAdminForm(forms.ModelForm):
    """Custom form for Department with multiple select for module rights"""
    module_rights = forms.MultipleChoiceField(
        choices=Department.APP_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select the modules/apps this department can access"
    )
    
    class Meta:
        model = Department
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Pre-select the existing module rights
            self.initial['module_rights'] = self.instance.module_rights
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Convert selected choices to list for JSONField
        instance.module_rights = self.cleaned_data.get('module_rights', [])
        if commit:
            instance.save()
        return instance


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    form = DepartmentAdminForm
    list_display = ['name', 'get_modules_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'display_module_names']
    autocomplete_fields = []  # Enable autocomplete for this model
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Module Access Rights', {
            'fields': ('module_rights', 'display_module_names'),
            'description': 'Select which modules/apps users in this department can access'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_modules_count(self, obj):
        """Display count of accessible modules"""
        return len(obj.module_rights)
    get_modules_count.short_description = 'Modules Count'
    
    def display_module_names(self, obj):
        """Display human-readable module names"""
        if obj.pk:
            names = obj.get_module_names()
            return ', '.join(names) if names else 'No modules assigned'
        return 'Save to see module names'
    display_module_names.short_description = 'Accessible Modules'

