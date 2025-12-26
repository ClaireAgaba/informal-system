from django.contrib import admin
from .models import ModularResult, FormalResult, WorkersPasResult


@admin.register(ModularResult)
class ModularResultAdmin(admin.ModelAdmin):
    list_display = [
        'candidate',
        'assessment_series',
        'module',
        'type',
        'mark',
        'grade',
        'comment',
        'status',
        'entered_by',
        'entered_at'
    ]
    list_filter = [
        'assessment_series',
        'type',
        'status',
        'entered_at'
    ]
    search_fields = [
        'candidate__first_name',
        'candidate__last_name',
        'candidate__registration_number',
        'module__module_code',
        'module__module_name'
    ]
    readonly_fields = ['entered_at', 'updated_at', 'grade', 'comment']
    
    fieldsets = (
        ('Candidate Information', {
            'fields': ('candidate', 'assessment_series')
        }),
        ('Module & Assessment', {
            'fields': ('module', 'type')
        }),
        ('Results', {
            'fields': ('mark', 'grade', 'comment', 'status')
        }),
        ('Metadata', {
            'fields': ('entered_by', 'entered_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def grade(self, obj):
        """Display calculated grade"""
        return obj.grade or '-'
    grade.short_description = 'Grade'
    
    def comment(self, obj):
        """Display calculated comment"""
        return obj.comment or '-'
    comment.short_description = 'Comment'
    
    # Allow filtering by candidate
    autocomplete_fields = ['candidate', 'module']
    
    # Order by most recent first
    ordering = ['-entered_at']


@admin.register(FormalResult)
class FormalResultAdmin(admin.ModelAdmin):
    list_display = [
        'candidate',
        'assessment_series',
        'level',
        'get_exam_or_paper',
        'type',
        'mark',
        'get_grade',
        'get_comment',
        'status',
        'entered_by',
        'entered_at',
    ]
    
    list_filter = [
        'assessment_series',
        'level',
        'type',
        'status',
        'entered_at',
    ]
    
    search_fields = [
        'candidate__full_name',
        'candidate__registration_number',
        'exam__module_name',
        'paper__paper_name',
    ]
    
    readonly_fields = [
        'get_grade',
        'get_comment',
        'entered_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Candidate Information', {
            'fields': ('candidate', 'assessment_series', 'level')
        }),
        ('Assessment Details', {
            'fields': ('exam', 'paper', 'type', 'mark', 'status')
        }),
        ('Calculated Fields', {
            'fields': ('get_grade', 'get_comment'),
            'classes': ('collapse',)
        }),
        ('Meta Information', {
            'fields': ('entered_by', 'entered_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_exam_or_paper(self, obj):
        """Display exam or paper name"""
        if obj.exam:
            return obj.exam.module_name
        elif obj.paper:
            return obj.paper.paper_name
        return '-'
    get_exam_or_paper.short_description = 'Exam/Paper'
    
    def get_grade(self, obj):
        """Display calculated grade"""
        return obj.grade or '-'
    get_grade.short_description = 'Grade'
    
    def get_comment(self, obj):
        """Display comment"""
        return obj.comment or '-'
    get_comment.short_description = 'Comment'
    
    # Order by most recent first
    ordering = ['-entered_at']


@admin.register(WorkersPasResult)
class WorkersPasResultAdmin(admin.ModelAdmin):
    list_display = [
        'candidate',
        'assessment_series',
        'level',
        'get_module',
        'get_paper',
        'type',
        'mark',
        'get_grade',
        'get_comment',
        'status',
        'entered_by',
        'entered_at',
    ]
    
    list_filter = [
        'assessment_series',
        'level',
        'status',
        'entered_at',
    ]
    
    search_fields = [
        'candidate__full_name',
        'candidate__registration_number',
        'paper__paper_code',
        'paper__paper_name',
        'module__module_code',
        'module__module_name',
    ]
    
    readonly_fields = [
        'type',
        'get_grade',
        'get_comment',
        'entered_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Candidate Information', {
            'fields': ('candidate', 'assessment_series')
        }),
        ('Assessment Details', {
            'fields': ('level', 'module', 'paper', 'type'),
            'description': 'Type is always "Practical" for Worker\'s PAS assessments'
        }),
        ('Results', {
            'fields': ('mark', 'status', 'get_grade', 'get_comment')
        }),
        ('Meta Information', {
            'fields': ('entered_by', 'entered_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    autocomplete_fields = ['candidate', 'level', 'module', 'paper']
    
    def get_module(self, obj):
        """Display module code and name"""
        if obj.module:
            return f"{obj.module.module_code} - {obj.module.module_name}"
        return '-'
    get_module.short_description = 'Module'
    get_module.admin_order_field = 'module__module_code'
    
    def get_paper(self, obj):
        """Display paper code and name"""
        if obj.paper:
            return f"{obj.paper.paper_code} - {obj.paper.paper_name}"
        return '-'
    get_paper.short_description = 'Paper'
    get_paper.admin_order_field = 'paper__paper_code'
    
    def get_grade(self, obj):
        """Display calculated grade"""
        return obj.grade or '-'
    get_grade.short_description = 'Grade'
    
    def get_comment(self, obj):
        """Display comment"""
        return obj.comment or '-'
    get_comment.short_description = 'Comment'
    
    # Order by most recent first
    ordering = ['-entered_at']
    
    def get_queryset(self, request):
        """Optimize queries with select_related"""
        return super().get_queryset(request).select_related(
            'candidate',
            'assessment_series',
            'level',
            'module',
            'paper',
            'entered_by'
        )
