from django.db import models
from configurations.models import District, Village


class AssessmentCenter(models.Model):
    """
    Model for managing assessment centers
    """
    CATEGORY_CHOICES = (
        ('VTI', 'Vocational Training Institute'),
        ('TTI', 'Technical Training Institute'),
        ('workplace', 'Workplace'),
    )
    
    center_number = models.CharField(max_length=50, unique=True, help_text="Enter a unique center number (e.g., UVT001)")
    center_name = models.CharField(max_length=200, help_text="Enter the full name of the assessment center")
    assessment_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, related_name='assessment_centers')
    village = models.ForeignKey(Village, on_delete=models.SET_NULL, null=True, blank=True, related_name='assessment_centers', help_text="You can add the village later during editing if needed")
    contact_1 = models.CharField(max_length=15, blank=True, verbose_name='Contact 1', help_text="Phone number or contact information for the center (optional)")
    contact_2 = models.CharField(max_length=15, blank=True, verbose_name='Contact 2', help_text="Secondary contact (optional)")
    has_branches = models.BooleanField(default=False, verbose_name='Has Branches?', help_text="Check if this center will have multiple branches in different locations")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['center_number']
        verbose_name = 'Assessment Center'
        verbose_name_plural = 'Assessment Centers'
        indexes = [
            models.Index(fields=['center_number']),
            models.Index(fields=['assessment_category']),
            models.Index(fields=['district']),
        ]
    
    def __str__(self):
        return f"{self.center_number} - {self.center_name}"
    
    def get_full_location(self):
        """Return full location string"""
        location_parts = []
        if self.village:
            location_parts.append(self.village.name)
        if self.district:
            location_parts.append(self.district.name)
        return ', '.join(location_parts) if location_parts else 'Location not set'
    
    def get_branches_count(self):
        """Return count of branches"""
        return self.branches.count()


class CenterBranch(models.Model):
    """
    Model for managing assessment center branches
    Branch name is inherited from the main center
    """
    assessment_center = models.ForeignKey(AssessmentCenter, on_delete=models.CASCADE, related_name='branches')
    branch_code = models.CharField(max_length=50, unique=True, help_text="Enter a unique branch code (e.g., UVT001-B1)")
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, related_name='center_branches', help_text="Select the district where this branch is located")
    village = models.ForeignKey(Village, on_delete=models.SET_NULL, null=True, blank=True, related_name='center_branches', help_text="Select the village where this branch is located")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['branch_code']
        verbose_name = 'Center Branch'
        verbose_name_plural = 'Center Branches'
        indexes = [
            models.Index(fields=['assessment_center']),
            models.Index(fields=['branch_code']),
        ]
    
    def __str__(self):
        return f"{self.assessment_center.center_name} - {self.branch_code}"
    
    def get_full_location(self):
        """Return full location string"""
        location_parts = []
        if self.village:
            location_parts.append(self.village.name)
        if self.district:
            location_parts.append(self.district.name)
        return ', '.join(location_parts) if location_parts else 'Location not set'
    
    @property
    def branch_name(self):
        """Branch name is same as main center name"""
        return self.assessment_center.center_name