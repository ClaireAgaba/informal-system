from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from candidates.models import Candidate
from assessment_series.models import AssessmentSeries
from assessment_centers.models import AssessmentCenter


class CandidateFee(models.Model):
    """Model for tracking individual candidate fees"""
    
    PAYMENT_STATUS_CHOICES = [
        ('not_paid', 'Not Paid'),
        ('pending_approval', 'Pending Approval'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ]
    
    ATTEMPT_STATUS_CHOICES = [
        ('no_attempt', 'No Attempt'),
        ('failed', 'Failed'),
        ('pending_approval', 'Pending Approval'),
        ('successful', 'Successful'),
    ]
    
    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('marked', 'Marked as Paid'),
        ('approved', 'Approved'),
    ]
    
    PAYMENT_REFERENCE_CHOICES = [
        ('bulk_payment', 'Bulk Payment'),
        ('via_schoolpay', 'Via SchoolPay'),
    ]
    
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='fees')
    assessment_series = models.ForeignKey(AssessmentSeries, on_delete=models.CASCADE, related_name='candidate_fees')
    payment_code = models.CharField(max_length=100, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='not_paid')
    attempt_status = models.CharField(max_length=20, choices=ATTEMPT_STATUS_CHOICES, default='no_attempt')
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    payment_reference = models.CharField(max_length=20, choices=PAYMENT_REFERENCE_CHOICES, null=True, blank=True)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='marked_fees')
    marked_date = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_fees')
    approved_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'candidate_fees'
        ordering = ['-created_at']
        verbose_name = 'Candidate Fee'
        verbose_name_plural = 'Candidate Fees'
    
    def __str__(self):
        return f"{self.candidate.registration_number} - {self.payment_code}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate amount_due
        self.amount_due = self.total_amount - self.amount_paid
        super().save(*args, **kwargs)


class CenterFee(models.Model):
    """Model for tracking assessment center fees"""
    
    assessment_series = models.ForeignKey(AssessmentSeries, on_delete=models.CASCADE, related_name='center_fees')
    assessment_center = models.ForeignKey(AssessmentCenter, on_delete=models.CASCADE, related_name='fees')
    total_candidates = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00'))])
    amount_due = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'center_fees'
        ordering = ['-created_at']
        verbose_name = 'Center Fee'
        verbose_name_plural = 'Center Fees'
        unique_together = ['assessment_series', 'assessment_center']
    
    def __str__(self):
        return f"{self.assessment_center.center_name} - {self.assessment_series.name}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate amount_due
        self.amount_due = self.total_amount - self.amount_paid
        super().save(*args, **kwargs)
