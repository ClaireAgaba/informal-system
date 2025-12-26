from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings


class ModularResult(models.Model):
    """
    Model for storing modular candidate results
    Each record represents a module result for a candidate
    """
    STATUS_CHOICES = (
        ('normal', 'Normal'),
        ('retake', 'Retake'),
        ('missing', 'Missing'),
    )
    
    TYPE_CHOICES = (
        ('theory', 'Theory'),
        ('practical', 'Practical'),
    )
    
    candidate = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.CASCADE,
        related_name='modular_results'
    )
    assessment_series = models.ForeignKey(
        'assessment_series.AssessmentSeries',
        on_delete=models.CASCADE,
        related_name='modular_results'
    )
    module = models.ForeignKey(
        'occupations.OccupationModule',
        on_delete=models.CASCADE,
        related_name='results'
    )
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='practical',
        help_text='Theory or Practical'
    )
    mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(-1), MaxValueValidator(100)],
        help_text='Mark scored (0-100, -1 for missing)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='normal',
        help_text='Normal for first attempt, Retake for second attempt, Missing if absent'
    )
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entered_modular_results'
    )
    entered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['assessment_series', 'module']
        verbose_name = 'Modular Result'
        verbose_name_plural = 'Modular Results'
        unique_together = ['candidate', 'assessment_series', 'module', 'type']
    
    def __str__(self):
        return f"{self.candidate.full_name} - {self.module.module_name} ({self.type})"
    
    @property
    def grade(self):
        """Calculate grade based on mark and type"""
        if self.mark is None:
            return None
        
        # -1 represents missing mark
        if self.mark == -1:
            return None
        
        if self.type == 'practical':
            # Practical grading
            if self.mark >= 90:
                return 'A+'
            elif self.mark >= 85:
                return 'A'
            elif self.mark >= 75:
                return 'B+'
            elif self.mark >= 65:
                return 'B'
            elif self.mark >= 60:
                return 'B-'
            elif self.mark >= 55:
                return 'C'
            elif self.mark >= 50:
                return 'C-'
            elif self.mark >= 40:
                return 'D'
            elif self.mark >= 30:
                return 'D-'
            else:
                return 'E'
        else:
            # Theory grading
            if self.mark >= 85:
                return 'A+'
            elif self.mark >= 80:
                return 'A'
            elif self.mark >= 70:
                return 'B'
            elif self.mark >= 60:
                return 'B-'
            elif self.mark >= 50:
                return 'C'
            elif self.mark >= 40:
                return 'C-'
            elif self.mark >= 30:
                return 'D'
            else:
                return 'E'
    
    @property
    def is_passing(self):
        """Check if mark is passing"""
        if self.mark is None or self.mark == -1:
            return False
        
        pass_mark = 55 if self.type == 'practical' else 50
        return self.mark >= pass_mark
    
    @property
    def comment(self):
        """Get comment based on pass/fail"""
        if self.mark is None:
            return None
        
        # -1 represents missing mark
        if self.mark == -1:
            return 'Missing'
        
        return 'Success' if self.is_passing else 'Not Successful'


class FormalResult(models.Model):
    """
    Model for storing formal assessment results
    Supports both module-based and paper-based structures
    """
    STATUS_CHOICES = (
        ('normal', 'Normal'),
        ('retake', 'Retake'),
        ('missing', 'Missing'),
    )
    
    TYPE_CHOICES = (
        ('theory', 'Theory'),
        ('practical', 'Practical'),
    )
    
    candidate = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.CASCADE,
        related_name='formal_results'
    )
    assessment_series = models.ForeignKey(
        'assessment_series.AssessmentSeries',
        on_delete=models.CASCADE,
        related_name='formal_results'
    )
    level = models.ForeignKey(
        'occupations.OccupationLevel',
        on_delete=models.CASCADE,
        related_name='formal_results'
    )
    
    # For module-based structure (both theory and practical required)
    exam = models.ForeignKey(
        'occupations.OccupationModule',
        on_delete=models.CASCADE,
        related_name='formal_results',
        null=True,
        blank=True,
        help_text='For module-based structure'
    )
    
    # For paper-based structure (either theory or practical)
    paper = models.ForeignKey(
        'occupations.OccupationPaper',
        on_delete=models.CASCADE,
        related_name='formal_results',
        null=True,
        blank=True,
        help_text='For paper-based structure'
    )
    
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        help_text='Theory or Practical'
    )
    mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(-1), MaxValueValidator(100)],
        help_text='Mark scored (0-100, -1 for missing)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='normal',
        help_text='Normal for first attempt, Retake for second attempt, Missing if absent'
    )
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entered_formal_results'
    )
    entered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['assessment_series', 'level']
        verbose_name = 'Formal Result'
        verbose_name_plural = 'Formal Results'
    
    def __str__(self):
        if self.exam:
            return f"{self.candidate.full_name} - {self.exam.module_name} ({self.type})"
        elif self.paper:
            return f"{self.candidate.full_name} - {self.paper.paper_name} ({self.type})"
        return f"{self.candidate.full_name} - {self.level.level_name}"
    
    @property
    def grade(self):
        """Calculate grade based on mark and type"""
        if self.mark is None:
            return None
        
        # -1 represents missing mark
        if self.mark == -1:
            return None
        
        if self.type == 'practical':
            # Practical grading
            if self.mark >= 90:
                return 'A+'
            elif self.mark >= 85:
                return 'A'
            elif self.mark >= 75:
                return 'B+'
            elif self.mark >= 65:
                return 'B'
            elif self.mark >= 60:
                return 'B-'
            elif self.mark >= 55:
                return 'C'
            elif self.mark >= 50:
                return 'C-'
            elif self.mark >= 40:
                return 'D'
            elif self.mark >= 30:
                return 'D-'
            else:
                return 'E'
        else:
            # Theory grading
            if self.mark >= 85:
                return 'A+'
            elif self.mark >= 80:
                return 'A'
            elif self.mark >= 70:
                return 'B'
            elif self.mark >= 60:
                return 'B-'
            elif self.mark >= 50:
                return 'C'
            elif self.mark >= 40:
                return 'C-'
            elif self.mark >= 30:
                return 'D'
            else:
                return 'E'
    
    @property
    def is_passing(self):
        """Check if mark is passing"""
        if self.mark is None or self.mark == -1:
            return False
        
        pass_mark = 65 if self.type == 'practical' else 50
        return self.mark >= pass_mark
    
    @property
    def comment(self):
        """Get comment based on pass/fail"""
        if self.mark is None:
            return None
        
        # -1 represents missing mark
        if self.mark == -1:
            return 'Missing'
        
        return 'Successful' if self.is_passing else 'Not Successful'


class WorkersPasResult(models.Model):
    """
    Model for storing Worker's PAS/Informal assessment results
    All assessments are practical only
    """
    STATUS_CHOICES = (
        ('normal', 'Normal'),
        ('retake', 'Retake'),
        ('missing', 'Missing'),
    )
    
    candidate = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.CASCADE,
        related_name='workers_pas_results'
    )
    assessment_series = models.ForeignKey(
        'assessment_series.AssessmentSeries',
        on_delete=models.CASCADE,
        related_name='workers_pas_results'
    )
    level = models.ForeignKey(
        'occupations.OccupationLevel',
        on_delete=models.CASCADE,
        related_name='workers_pas_results',
        help_text='Level of the paper'
    )
    module = models.ForeignKey(
        'occupations.OccupationModule',
        on_delete=models.CASCADE,
        related_name='workers_pas_results',
        help_text='Module of the paper'
    )
    paper = models.ForeignKey(
        'occupations.OccupationPaper',
        on_delete=models.CASCADE,
        related_name='workers_pas_results',
        help_text='Paper being assessed'
    )
    # Type is always 'practical' for Workers PAS
    type = models.CharField(
        max_length=20,
        default='practical',
        editable=False,
        help_text='Always Practical for Workers PAS'
    )
    mark = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(-1), MaxValueValidator(100)],
        help_text='Mark scored (0-100, -1 for missing)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='normal',
        help_text='Normal for first attempt, Retake for second attempt, Missing if absent'
    )
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entered_workers_pas_results'
    )
    entered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['assessment_series', 'level', 'module', 'paper']
        verbose_name = "Worker's PAS Result"
        verbose_name_plural = "Worker's PAS Results"
        unique_together = ['candidate', 'assessment_series', 'paper']
    
    def __str__(self):
        return f"{self.candidate.full_name} - {self.paper.paper_name} (Practical)"
    
    @property
    def grade(self):
        """Calculate grade based on mark (practical grading)"""
        if self.mark is None:
            return None
        
        # -1 represents missing mark
        if self.mark == -1:
            return None
        
        # Practical grading
        if self.mark >= 90:
            return 'A+'
        elif self.mark >= 85:
            return 'A'
        elif self.mark >= 75:
            return 'B+'
        elif self.mark >= 65:
            return 'B'
        elif self.mark >= 60:
            return 'B-'
        elif self.mark >= 55:
            return 'C'
        elif self.mark >= 50:
            return 'C-'
        elif self.mark >= 40:
            return 'D'
        elif self.mark >= 30:
            return 'D-'
        else:
            return 'E'
    
    @property
    def is_passing(self):
        """Check if mark is passing (65% for practical)"""
        if self.mark is None or self.mark == -1:
            return False
        return self.mark >= 65
    
    @property
    def comment(self):
        """Get comment based on pass/fail"""
        if self.mark is None:
            return None
        
        # -1 represents missing mark
        if self.mark == -1:
            return 'Missing'
        
        return 'Successful' if self.is_passing else 'Not Successful'
