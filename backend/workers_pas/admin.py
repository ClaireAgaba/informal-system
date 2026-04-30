"""Admin registration for Worker's PAS books."""
from django.contrib import admin
from django.utils.html import format_html

from .models import WorkersPasBook


@admin.register(WorkersPasBook)
class WorkersPasBookAdmin(admin.ModelAdmin):
    list_display = [
        'book_number', 'candidate', 'occupation', 'assessment_series',
        'sequence_number', 'issued_date', 'reprint_count', 'has_pdf',
    ]
    list_filter = ['occupation', 'assessment_series', 'issued_date']
    search_fields = [
        'book_number', 'candidate__full_name',
        'candidate__registration_number',
    ]
    readonly_fields = [
        'book_number', 'sequence_number', 'full_label',
        'created_at', 'updated_at', 'pdf_link',
    ]
    autocomplete_fields = ['candidate', 'occupation', 'assessment_series']
    fieldsets = (
        ('Book', {
            'fields': ('book_number', 'full_label', 'sequence_number',
                       'issued_date', 'reprint_count'),
        }),
        ('Subject', {
            'fields': ('candidate', 'occupation', 'assessment_series'),
        }),
        ('PDF', {
            'fields': ('pdf_file', 'pdf_link'),
        }),
        ('Audit', {
            'fields': ('generated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def has_pdf(self, obj):
        return bool(obj.pdf_file)
    has_pdf.boolean = True
    has_pdf.short_description = 'PDF generated'

    def pdf_link(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">Download PDF</a>',
                               obj.pdf_file.url)
        return '-'
    pdf_link.short_description = 'PDF'
