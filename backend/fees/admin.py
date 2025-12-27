from django.contrib import admin
from .models import CandidateFee, CenterFee


@admin.register(CandidateFee)
class CandidateFeeAdmin(admin.ModelAdmin):
    list_display = ['payment_code', 'candidate', 'assessment_series', 'total_amount', 'amount_paid', 'amount_due', 'payment_status', 'attempt_status']
    list_filter = ['payment_status', 'attempt_status', 'assessment_series']
    search_fields = ['payment_code', 'candidate__registration_number', 'candidate__first_name', 'candidate__last_name']
    readonly_fields = ['amount_due', 'created_at', 'updated_at']


@admin.register(CenterFee)
class CenterFeeAdmin(admin.ModelAdmin):
    list_display = ['assessment_center', 'assessment_series', 'total_candidates', 'total_amount', 'amount_paid', 'amount_due']
    list_filter = ['assessment_series', 'assessment_center']
    search_fields = ['assessment_center__center_name']
    readonly_fields = ['amount_due', 'created_at', 'updated_at']
