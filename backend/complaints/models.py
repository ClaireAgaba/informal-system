from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone
from assessment_centers.models import AssessmentCenter
from assessment_series.models import AssessmentSeries
from occupations.models import Occupation
from users.models import User


class ComplaintCategory(models.Model):
    """Categories for complaints"""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Complaint Category'
        verbose_name_plural = 'Complaint Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Complaint(models.Model):
    """Model for tracking complaints from assessment centers"""
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ]

    # Auto-generated ticket number
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    
    # Complaint details
    category = models.ForeignKey(
        ComplaintCategory,
        on_delete=models.PROTECT,
        related_name='complaints'
    )
    exam_center = models.ForeignKey(
        AssessmentCenter,
        on_delete=models.CASCADE,
        related_name='complaints',
        null=True,
        blank=True
    )
    exam_series = models.ForeignKey(
        AssessmentSeries,
        on_delete=models.PROTECT,
        related_name='complaints',
        null=True,
        blank=True
    )
    program = models.ForeignKey(
        Occupation,
        on_delete=models.PROTECT,
        related_name='complaints',
        verbose_name='Program/Occupation',
        null=True,
        blank=True
    )
    
    # Additional details
    phone = models.CharField(max_length=20, blank=True)
    
    # Issue details
    issue_description = models.TextField()
    proof_of_complaint = models.FileField(
        upload_to='complaints/proofs/%Y/%m/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx']
        )]
    )
    
    # Status and assignment
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    helpdesk_team = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_complaints',
        limit_choices_to={'is_staff': True}
    )
    
    # Response tracking
    team_response = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_complaints'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Complaint'
        verbose_name_plural = 'Complaints'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket_number']),
            models.Index(fields=['status']),
            models.Index(fields=['exam_center']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.ticket_number} - {self.category}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            # Generate ticket number in format TKT{YY}{SERIAL}
            # YY = 2-digit year, SERIAL = 5-digit sequential number
            current_year = timezone.now().year
            year_suffix = str(current_year)[-2:]  # Last 2 digits of year
            
            # Get the last complaint for this year
            year_prefix = f'TKT{year_suffix}'
            last_complaint = Complaint.objects.filter(
                ticket_number__startswith=year_prefix
            ).order_by('-ticket_number').first()
            
            if last_complaint and last_complaint.ticket_number:
                # Extract the serial number (last 5 digits)
                last_serial = int(last_complaint.ticket_number[-5:])
                new_serial = last_serial + 1
            else:
                # First complaint of the year
                new_serial = 1
            
            # Format: TKT + YY + 5-digit serial (zero-padded)
            self.ticket_number = f'TKT{year_suffix}{new_serial:05d}'
        super().save(*args, **kwargs)


class ComplaintAttachment(models.Model):
    """Additional attachments for complaints"""
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(
        upload_to='complaints/attachments/%Y/%m/',
        validators=[FileExtensionValidator(
            allowed_extensions=['png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx']
        )]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Complaint Attachment'
        verbose_name_plural = 'Complaint Attachments'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Attachment for {self.complaint.ticket_number}"
