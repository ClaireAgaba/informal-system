from django.db import models


class Region(models.Model):
    """
    Model for managing regions
    """
    REGION_CHOICES = (
        ('central', 'Central'),
        ('western', 'Western'),
        ('eastern', 'Eastern'),
        ('northern', 'Northern'),
    )
    
    name = models.CharField(max_length=50, choices=REGION_CHOICES, unique=True)
    description = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Region'
        verbose_name_plural = 'Regions'
    
    def __str__(self):
        return self.get_name_display()


class District(models.Model):
    """
    Model for managing districts
    """
    name = models.CharField(max_length=100, unique=True, help_text="Enter the name of the district (max 100 characters)")
    region = models.CharField(max_length=50, choices=Region.REGION_CHOICES)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['region', 'name']
        verbose_name = 'District'
        verbose_name_plural = 'Districts'
        indexes = [
            models.Index(fields=['region']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_region_display()})"


class Village(models.Model):
    """
    Model for managing villages
    """
    name = models.CharField(max_length=100, help_text="Enter the name of the village")
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='villages')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['district', 'name']
        verbose_name = 'Village'
        verbose_name_plural = 'Villages'
        unique_together = ['name', 'district']
        indexes = [
            models.Index(fields=['district']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.district.name}"


class NatureOfDisability(models.Model):
    """
    Model for managing nature of disability types
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Nature of Disability'
        verbose_name_plural = 'Nature of Disabilities'
    
    def __str__(self):
        return self.name


class Department(models.Model):
    """
    Model for managing departments with module access rights
    """
    # Available Django apps/modules in the system
    APP_CHOICES = (
        ('users', 'User Management'),
        ('candidates', 'Candidate Management'),
        ('occupations', 'Occupation Management'),
        ('assessment_centers', 'Assessment Centers'),
        ('assessment_series', 'Assessment Series'),
        ('results', 'Results Management'),
        ('awards', 'Awards & Certificates'),
        ('reports', 'Reports'),
        ('complaints', 'Complaints'),
        ('statistics', 'Statistics'),
        ('configurations', 'System Configurations'),
        ('dit_migration', 'DIT Migration'),
    )
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Module access rights - stores list of app names user can access
    module_rights = models.JSONField(
        default=list,
        help_text="List of Django apps/modules this department has access to"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
    
    def __str__(self):
        return self.name
    
    def get_module_names(self):
        """Return human-readable names of accessible modules"""
        app_dict = dict(self.APP_CHOICES)
        return [app_dict.get(app, app) for app in self.module_rights]
    
    def has_module_access(self, app_name):
        """Check if department has access to a specific module"""
        return app_name in self.module_rights


class CenterRepresentative(models.Model):
    """
    Model for managing center representative designations
    e.g. Head of Center, Academic Registrar, Director of Studies
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Center Representative'
        verbose_name_plural = 'Center Representatives'

    def __str__(self):
        return self.name


class ReprintReason(models.Model):
    """
    Model for managing transcript reprint reasons
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    requires_duplicate_watermark = models.BooleanField(
        default=False,
        help_text="If checked, reprinted transcripts with this reason will have a 'DUPLICATE' watermark"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Reprint Reason'
        verbose_name_plural = 'Reprint Reasons'
    
    def __str__(self):
        return self.name


