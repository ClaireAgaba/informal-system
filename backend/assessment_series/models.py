from django.db import models
from django.core.exceptions import ValidationError


class AssessmentSeries(models.Model):
    """
    Model for managing assessment series/periods
    An assessment series represents a specific assessment period (e.g., "March 2024 Assessment")
    """
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name='Assessment Series Name',
        help_text='Enter a descriptive name for this assessment series (e.g., "March 2024 Assessment")'
    )
    
    start_date = models.DateField(
        verbose_name='Start Date',
        help_text='Assessment period begins'
    )
    
    end_date = models.DateField(
        verbose_name='End Date',
        help_text='Assessment period ends'
    )
    
    date_of_release = models.DateField(
        verbose_name='Results Release Date',
        help_text='Date when results will be released'
    )
    
    is_current = models.BooleanField(
        default=False,
        verbose_name='Set as Current Assessment Series',
        help_text='Mark this as the currently active assessment series. Only one series can be current at a time.'
    )
    
    results_released = models.BooleanField(
        default=False,
        verbose_name='Results Released',
        help_text='Toggle to release results to candidates and assessment centers'
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Assessment Series'
        verbose_name_plural = 'Assessment Series'
        indexes = [
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
            models.Index(fields=['is_current']),
            models.Index(fields=['results_released']),
        ]
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate assessment series data"""
        # Validate that end date is after start date
        if self.start_date and self.end_date:
            if self.end_date <= self.start_date:
                raise ValidationError({
                    'end_date': 'End date must be after the start date.'
                })
        
        # Validate that results release date is on or after end date
        if self.end_date and self.date_of_release:
            if self.date_of_release < self.end_date:
                raise ValidationError({
                    'date_of_release': 'Results release date should be on or after the end date.'
                })
        
        # Ensure only one series is marked as current
        if self.is_current:
            # Check if another series is already marked as current
            current_series = AssessmentSeries.objects.filter(is_current=True)
            if self.pk:
                current_series = current_series.exclude(pk=self.pk)
            
            if current_series.exists():
                raise ValidationError({
                    'is_current': 'Only one assessment series can be marked as current at a time. '
                                 f'"{current_series.first().name}" is currently marked as current.'
                })
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one current series"""
        # If this series is being set as current, unset all others
        if self.is_current:
            AssessmentSeries.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        
        super().save(*args, **kwargs)
    
    def get_duration_days(self):
        """Calculate the duration of the assessment series in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0
    
    def is_ongoing(self):
        """Check if the assessment series is currently ongoing"""
        if not self.start_date or not self.end_date:
            return False
        from datetime import date
        today = date.today()
        return self.start_date <= today <= self.end_date
    
    def is_upcoming(self):
        """Check if the assessment series is upcoming"""
        if not self.start_date:
            return False
        from datetime import date
        today = date.today()
        return self.start_date > today
    
    def is_completed(self):
        """Check if the assessment series has ended"""
        if not self.end_date:
            return False
        from datetime import date
        today = date.today()
        return self.end_date < today
    
    def can_release_results(self):
        """Check if results can be released (after end date)"""
        if not self.date_of_release:
            return False
        from datetime import date
        today = date.today()
        return today >= self.date_of_release
    
    def get_status(self):
        """Get the current status of the assessment series"""
        # Return 'Not Set' if dates are missing
        if not self.start_date or not self.end_date:
            return 'Not Set'
        
        if self.is_upcoming():
            return 'Upcoming'
        elif self.is_ongoing():
            return 'Ongoing'
        elif self.is_completed():
            if self.results_released:
                return 'Completed - Results Released'
            else:
                return 'Completed - Results Pending'
        return 'Unknown'
