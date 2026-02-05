from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Sector(models.Model):
    """
    Model for managing industry sectors
    """
    name = models.CharField(max_length=200, unique=True, verbose_name='Sector Name')
    description = models.TextField(blank=True, help_text="Provide a brief description of this sector (optional)")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Sector'
        verbose_name_plural = 'Sectors'
    
    def __str__(self):
        return self.name
    
    def get_occupations_count(self):
        """Return count of occupations in this sector"""
        return self.occupations.count()


class Occupation(models.Model):
    """
    Model for managing occupations/trades
    """
    CATEGORY_CHOICES = (
        ('formal', 'Formal'),
        ('workers_pas', "Worker's PAS"),
    )
    
    occ_code = models.CharField(max_length=50, unique=True, verbose_name='Occupation Code')
    occ_name = models.CharField(max_length=200, verbose_name='Occupation Name')
    occ_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name='Occupation Category')
    award = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name='Award',
        help_text="Award/Certificate title for this occupation (used on transcripts)"
    )
    sector = models.ForeignKey(
        Sector, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='occupations',
        help_text="Industry sector the occupation belongs to"
    )
    
    # Modular flag - only relevant for formal occupations
    has_modular = models.BooleanField(
        default=False, 
        verbose_name='Has Modular?',
        help_text="Tick if this occupation allows Modular registration (Level 1 only)"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['occ_code']
        verbose_name = 'Occupation'
        verbose_name_plural = 'Occupations'
        indexes = [
            models.Index(fields=['occ_code']),
            models.Index(fields=['occ_category']),
        ]
    
    def __str__(self):
        return f"{self.occ_code} - {self.occ_name}"
    
    def get_levels_count(self):
        """Return count of levels for this occupation"""
        return self.levels.count()
    
    def is_formal(self):
        """Check if occupation is formal category"""
        return self.occ_category == 'formal'
    
    def is_workers_pas(self):
        """Check if occupation is Worker's PAS category"""
        return self.occ_category == 'workers_pas'


class OccupationLevel(models.Model):
    """
    Model for managing occupation levels with billing information
    Levels can contain either modules or papers
    """
    STRUCTURE_TYPE_CHOICES = (
        ('modules', 'Modules'),
        ('papers', 'Papers'),
    )
    
    occupation = models.ForeignKey(Occupation, on_delete=models.CASCADE, related_name='levels')
    level_name = models.CharField(max_length=100, help_text="Enter level name (e.g., Level 1, Level 2, etc.)")
    structure_type = models.CharField(
        max_length=20, 
        choices=STRUCTURE_TYPE_CHOICES, 
        default='modules',
        help_text="Does this level contain modules or papers?"
    )
    
    # Billing Types (5 fee types)
    formal_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Formal Fee (UGX)',
        help_text="Fee for Formal registration (varies by level)"
    )
    
    workers_pas_base_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Worker's PAS Base Fee (UGX)",
        help_text="Fee for Worker's PAS registration (Flat rate across levels)"
    )
    
    workers_pas_per_module_fee = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Worker's PAS Per-Module Fee (UGX)",
        help_text="Fee per module for Worker's PAS registration (multiplied by modules enrolled)"
    )
    
    modular_fee_single_module = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Modular Fee - Single Module (UGX)',
        help_text="Fee for Modular registration with 1 module"
    )
    
    modular_fee_double_module = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Modular Fee - Double Module (UGX)',
        help_text="Fee for Modular registration with 2 modules"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['occupation', 'level_name']
        verbose_name = 'Occupation Level'
        verbose_name_plural = 'Occupation Levels'
        unique_together = ['occupation', 'level_name']
        indexes = [
            models.Index(fields=['occupation']),
        ]
    
    def __str__(self):
        return f"{self.occupation.occ_code} - {self.level_name}"
    
    def get_structure_display_text(self):
        """Return structure type display text"""
        return self.get_structure_type_display()


class OccupationModule(models.Model):
    """
    Model for managing modules within occupation levels
    """
    module_code = models.CharField(max_length=50, unique=True, verbose_name='Module Code')
    module_name = models.CharField(max_length=200, verbose_name='Module Name')
    
    occupation = models.ForeignKey(
        Occupation, 
        on_delete=models.CASCADE, 
        related_name='modules',
        help_text="Select the occupation this module belongs to"
    )
    
    level = models.ForeignKey(
        OccupationLevel, 
        on_delete=models.CASCADE, 
        related_name='modules',
        help_text="Select the level for this module"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['occupation', 'level', 'module_code']
        verbose_name = 'Occupation Module'
        verbose_name_plural = 'Occupation Modules'
        unique_together = ['occupation', 'module_code']
        indexes = [
            models.Index(fields=['occupation']),
            models.Index(fields=['level']),
            models.Index(fields=['module_code']),
        ]
    
    def __str__(self):
        return f"{self.module_code} - {self.module_name}"
    
    def clean(self):
        """Validate that the level belongs to the selected occupation"""
        from django.core.exceptions import ValidationError
        if self.level and self.occupation:
            if self.level.occupation != self.occupation:
                raise ValidationError({
                    'level': f'The selected level does not belong to {self.occupation.occ_name}'
                })


class ModuleLWA(models.Model):
    """
    Model for Learning Working Assignments (LWAs) within modules
    """
    module = models.ForeignKey(
        OccupationModule,
        on_delete=models.CASCADE,
        related_name='lwas',
        help_text="Select the module this LWA belongs to"
    )
    lwa_name = models.CharField(max_length=200, verbose_name='LWA Name')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['module', 'lwa_name']
        verbose_name = 'Module LWA'
        verbose_name_plural = 'Module LWAs'
        indexes = [
            models.Index(fields=['module']),
        ]
    
    def __str__(self):
        return f"{self.module.module_code} - {self.lwa_name}"


class OccupationPaper(models.Model):
    """
    Model for managing papers within occupation levels
    """
    PAPER_TYPE_CHOICES = (
        ('theory', 'Theory'),
        ('practical', 'Practical'),
    )
    
    paper_code = models.CharField(max_length=50, unique=True, verbose_name='Paper Code')
    paper_name = models.CharField(max_length=200, verbose_name='Paper Name')
    
    occupation = models.ForeignKey(
        Occupation, 
        on_delete=models.CASCADE, 
        related_name='papers',
        help_text="Select the occupation this paper belongs to"
    )
    
    level = models.ForeignKey(
        OccupationLevel, 
        on_delete=models.CASCADE, 
        related_name='papers',
        help_text="Select the level for this paper"
    )
    
    module = models.ForeignKey(
        OccupationModule,
        on_delete=models.CASCADE,
        related_name='papers',
        null=True,
        blank=True,
        help_text="Select the module this paper belongs to (for Worker's PAS only)"
    )
    
    paper_type = models.CharField(
        max_length=20, 
        choices=PAPER_TYPE_CHOICES,
        verbose_name='Paper Type',
        help_text="Select whether this is a Theory or Practical paper"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['occupation', 'level', 'paper_code']
        verbose_name = 'Occupation Paper'
        verbose_name_plural = 'Occupation Papers'
        unique_together = ['occupation', 'paper_code']
        indexes = [
            models.Index(fields=['occupation']),
            models.Index(fields=['level']),
            models.Index(fields=['paper_code']),
            models.Index(fields=['paper_type']),
        ]
    
    def __str__(self):
        return f"{self.paper_code} - {self.paper_name} ({self.get_paper_type_display()})"
    
    def clean(self):
        """Validate that the level belongs to the selected occupation"""
        from django.core.exceptions import ValidationError
        if self.level and self.occupation:
            if self.level.occupation != self.occupation:
                raise ValidationError({
                    'level': f'The selected level does not belong to {self.occupation.occ_name}'
                })