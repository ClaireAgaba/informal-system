from django.db import models


class SystemStatistic(models.Model):
    """
    Model for storing system-wide statistics
    """
    STATISTIC_TYPES = (
        ('candidate_count', 'Total Candidates'),
        ('registration_count', 'Total Registrations'),
        ('assessment_count', 'Total Assessments'),
        ('pass_rate', 'Pass Rate'),
        ('center_utilization', 'Center Utilization'),
        ('revenue', 'Revenue'),
    )
    
    statistic_type = models.CharField(max_length=30, choices=STATISTIC_TYPES)
    value = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Optional filters
    year = models.IntegerField(blank=True, null=True)
    month = models.IntegerField(blank=True, null=True)
    region = models.CharField(max_length=100, blank=True)
    
    metadata = models.JSONField(default=dict, blank=True)
    
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_at']
        verbose_name = 'System Statistic'
        verbose_name_plural = 'System Statistics'
    
    def __str__(self):
        return f"{self.get_statistic_type_display()} - {self.value} ({self.recorded_at.strftime('%Y-%m-%d')})"
