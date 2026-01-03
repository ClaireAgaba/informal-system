from django.contrib import admin
from .models import Complaint, ComplaintCategory, ComplaintAttachment


@admin.register(ComplaintCategory)
class ComplaintCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']


class ComplaintAttachmentInline(admin.TabularInline):
    model = ComplaintAttachment
    extra = 0
    readonly_fields = ['uploaded_at', 'uploaded_by']


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'category', 'exam_center', 'status', 'helpdesk_team', 'created_at']
    list_filter = ['status', 'category', 'exam_center', 'created_at']
    search_fields = ['ticket_number', 'issue_description', 'exam_center__name']
    readonly_fields = ['ticket_number', 'created_by', 'created_at', 'updated_at']
    inlines = [ComplaintAttachmentInline]
    
    fieldsets = (
        ('Ticket Information', {
            'fields': ('ticket_number', 'status', 'helpdesk_team')
        }),
        ('Complaint Details', {
            'fields': ('category', 'exam_center', 'exam_series', 'program', 'phone')
        }),
        ('Issue Description', {
            'fields': ('issue_description', 'proof_of_complaint')
        }),
        ('Response', {
            'fields': ('team_response',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when creating new complaint
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
