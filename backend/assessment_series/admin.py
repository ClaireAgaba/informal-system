from django.contrib import admin
from django.utils.html import format_html
from .models import AssessmentSeries


@admin.register(AssessmentSeries)
class AssessmentSeriesAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'start_date', 'end_date', 'date_of_release',
        'get_status_display', 'is_current', 'results_released', 'created_at'
    ]
    
    list_filter = [
        'is_current', 'results_released', 'is_active',
        'start_date', 'end_date', 'created_at'
    ]
    
    search_fields = ['name']
    
    readonly_fields = ['created_at', 'updated_at', 'get_duration', 'get_status_display']
    
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Assessment Series Information', {
            'fields': ('name',),
            'description': 'Enter a descriptive name for this assessment series (e.g., "March 2024 Assessment")'
        }),
        ('Assessment Dates', {
            'fields': (
                ('start_date', 'end_date'),
                'date_of_release',
                'get_duration'
            ),
            'description': 'The end date must be after the start date. Results release date should be on or after the end date.'
        }),
        ('Status & Settings', {
            'fields': (
                'is_current',
                'results_released',
                'is_active',
                'get_status_display'
            ),
            'description': 'Only one assessment series can be marked as current at a time.'
        }),
        ('Timestamps', {
            'fields': (('created_at', 'updated_at'),),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'set_as_current', 'release_results', 'unrelease_results',
        'activate_series', 'deactivate_series'
    ]
    
    def get_status_display(self, obj):
        """Display the current status with color coding"""
        status = obj.get_status()
        color_map = {
            'Not Set': '#7f8c8d',   # Dark Gray
            'Upcoming': '#3498db',  # Blue
            'Ongoing': '#27ae60',   # Green
            'Completed - Results Released': '#95a5a6',  # Gray
            'Completed - Results Pending': '#e67e22',   # Orange
        }
        color = color_map.get(status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    get_status_display.short_description = 'Status'
    
    def get_duration(self, obj):
        """Display the duration of the assessment series"""
        days = obj.get_duration_days()
        return f"{days} days"
    get_duration.short_description = 'Duration'
    
    # Admin Actions
    def set_as_current(self, request, queryset):
        """Set selected series as current (only one can be selected)"""
        if queryset.count() > 1:
            self.message_user(
                request,
                'You can only set one assessment series as current at a time.',
                level='error'
            )
            return
        
        series = queryset.first()
        # Unset all other current series
        AssessmentSeries.objects.filter(is_current=True).update(is_current=False)
        # Set this one as current
        series.is_current = True
        series.save()
        
        self.message_user(request, f'"{series.name}" is now set as the current assessment series.')
    set_as_current.short_description = 'Set as current assessment series'
    
    def release_results(self, request, queryset):
        """Release results for selected series"""
        updated = queryset.update(results_released=True)
        self.message_user(request, f'Results released for {updated} assessment series.')
    release_results.short_description = 'Release results'
    
    def unrelease_results(self, request, queryset):
        """Unrelease results for selected series"""
        updated = queryset.update(results_released=False)
        self.message_user(request, f'Results unreleased for {updated} assessment series.')
    unrelease_results.short_description = 'Unrelease results'
    
    def activate_series(self, request, queryset):
        """Activate selected series"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} assessment series activated.')
    activate_series.short_description = 'Activate selected series'
    
    def deactivate_series(self, request, queryset):
        """Deactivate selected series"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} assessment series deactivated.')
    deactivate_series.short_description = 'Deactivate selected series'
