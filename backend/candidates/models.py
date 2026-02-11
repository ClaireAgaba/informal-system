from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from datetime import date
from decimal import Decimal
from django_countries.fields import CountryField
from configurations.models import District, Village, NatureOfDisability
from assessment_centers.models import AssessmentCenter, CenterBranch
from occupations.models import Occupation
from users.models import Staff


class Candidate(models.Model):
    """
    Model for managing candidate registrations
    """
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    
    REGISTRATION_CATEGORY_CHOICES = (
        ('modular', 'Modular'),
        ('formal', 'Formal'),
        ('workers_pas', "Worker's PAS"),
    )
    
    INTAKE_CHOICES = (
        ('M', 'March'),
        ('J', 'June'),
        ('S', 'September'),
        ('D', 'December'),
        ('A', 'August'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('completed', 'Completed'),
    )
    
    VERIFICATION_STATUS_CHOICES = (
        ('pending_verification', 'Pending Verification'),
        ('verified', 'Verified'),
        ('declined', 'Declined'),
    )
    
    # Registration Number (auto-generated on submission)
    registration_number = models.CharField(
        max_length=50, 
        unique=True,
        null=True,
        blank=True,
        verbose_name='Registration Number',
        help_text='Unique registration number generated when candidate is submitted'
    )
    
    # Payment Code (auto-generated with registration number)
    payment_code = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Payment Code',
        help_text='Unique payment code in format: IUV00225000001'
    )
    
    # Transcript Serial Number
    transcript_serial_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Transcript Serial Number',
        help_text='Unique transcript serial number (TR SNo)'
    )
    
    # Transcript Collection Tracking
    transcript_collected = models.BooleanField(
        default=False,
        verbose_name='Transcript Collected',
        help_text='Whether the printed transcript has been collected'
    )
    transcript_collector_name = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name='Collector Name',
        help_text='Name of the person who collected the transcript'
    )
    transcript_collector_phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name='Collector Phone',
        help_text='Phone number of the person who collected the transcript'
    )
    transcript_collection_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Collection Date',
        help_text='Date when the transcript was collected'
    )
    
    # Submission Status
    is_submitted = models.BooleanField(
        default=False,
        verbose_name='Is Submitted',
        help_text='Whether the candidate registration has been submitted'
    )
    
    # Personal Information
    full_name = models.CharField(max_length=200, verbose_name='Full Name')
    date_of_birth = models.DateField(verbose_name='Date of Birth')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    nationality = models.CharField(
        max_length=100, 
        default='Uganda',
        verbose_name='Nationality (Legacy)',
        help_text='Legacy field - will be migrated to candidate_country'
    )
    candidate_country = CountryField(
        blank=True,
        null=True,
        default='UG',
        verbose_name='Country',
        help_text='Country of nationality'
    )
    
    # Refugee Information
    is_refugee = models.BooleanField(default=False, verbose_name='Is Refugee?')
    refugee_number = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='Refugee Identification Number'
    )
    
    # Contact & Location
    contact = models.CharField(max_length=20, verbose_name='Contact Number')
    district = models.ForeignKey(
        District, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='candidates',
        verbose_name='Home District'
    )
    village = models.ForeignKey(
        Village, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='candidates',
        verbose_name='Village'
    )
    
    # Disability Information
    has_disability = models.BooleanField(default=False, verbose_name='Has Disability?')
    nature_of_disability = models.ForeignKey(
        NatureOfDisability,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidates',
        verbose_name='Nature of Disability'
    )
    disability_specification = models.TextField(
        blank=True,
        verbose_name='Disability Specification',
        help_text='Provide specific details about the disability'
    )
    
    # Assessment Information
    assessment_center = models.ForeignKey(
        AssessmentCenter,
        on_delete=models.SET_NULL,
        null=True,
        related_name='candidates',
        verbose_name='Assessment Center'
    )
    assessment_center_branch = models.ForeignKey(
        CenterBranch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidates',
        verbose_name='Assessment Center Branch'
    )
    entry_year = models.IntegerField(verbose_name='Entry Year')
    intake = models.CharField(max_length=1, choices=INTAKE_CHOICES, verbose_name='Assessment Intake')
    
    # Registration Category & Occupation
    registration_category = models.CharField(
        max_length=20, 
        choices=REGISTRATION_CATEGORY_CHOICES,
        verbose_name='Registration Category'
    )
    occupation = models.ForeignKey(
        Occupation,
        on_delete=models.SET_NULL,
        null=True,
        related_name='candidates',
        verbose_name='Occupation'
    )
    
    # Assessment Language
    preferred_assessment_language = models.CharField(
        max_length=50,
        default='English',
        verbose_name='Preferred Assessment Language'
    )
    
    # Assessment Dates
    start_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Training Start Date'
    )
    finish_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Training Finish Date'
    )
    assessment_date = models.DateField(
        null=True, 
        blank=True,
        verbose_name='Assessment Date'
    )
    
    # Staff Assignment
    created_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_candidates',
        verbose_name='Created By'
    )
    updated_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_candidates',
        verbose_name='Updated By'
    )
    
    # Enrollment Level (for tracking progress)
    enrollment_level = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Enrollment Level',
        help_text='Current level of enrollment'
    )
    
    # Registration Number (for legacy systems)
    reg_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Legacy Registration Number'
    )
    
    # Status & Verification
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Account Status'
    )
    block_portal_results = models.BooleanField(
        default=False,
        verbose_name='Block Portal Results',
        help_text='If checked, this candidate cannot view results in the portal'
    )
    
    # Fees & Payment
    fees_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Outstanding Fees Balance'
    )
    
    # Modular-specific fields
    modular_module_count = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Modular Module Count',
        help_text='For Modular candidates, specify number of modules (1 or 2)'
    )
    modular_billing_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Modular Billing Amount'
    )
    
    # Document Uploads
    passport_photo = models.ImageField(
        upload_to='candidates/photos/',
        null=True,
        blank=True,
        verbose_name='Passport Photo'
    )
    identification_document = models.FileField(
        upload_to='candidates/documents/identification/',
        null=True,
        blank=True,
        verbose_name='Identification Document',
        help_text='National ID, Birth Certificate, or other identification (PNG, JPG, PDF max 10MB)'
    )
    qualification_document = models.FileField(
        upload_to='candidates/documents/qualifications/',
        null=True,
        blank=True,
        verbose_name='Qualification Document',
        help_text='Relevant qualifications for Full Occupation candidates (PNG, JPG, or PDF max 10MB)'
    )
    
    # Verification
    verification_status = models.CharField(
        max_length=30,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending_verification',
        verbose_name='Verification Status'
    )
    verification_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Verification Date'
    )
    verified_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_candidates',
        verbose_name='Verified By'
    )
    decline_reason = models.TextField(
        blank=True,
        verbose_name='Decline Reason',
        help_text='Reason for declining candidate (when status is declined)'
    )
    
    # Payment Tracking
    payment_cleared = models.BooleanField(
        default=False,
        verbose_name='Payment Cleared',
        help_text='TRUE if this candidate\'s fees have been cleared/paid. Proceed to decision and process audit trail'
    )
    payment_cleared_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Payment Cleared Date'
    )
    payment_cleared_by = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_cleared_candidates',
        verbose_name='Payment Cleared By'
    )
    payment_amount_cleared = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Payment Amount Cleared'
    )
    payment_center_series_ref = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Payment Center Series Reference',
        help_text='Reference to center series payment transaction (if center_series_id)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Candidate'
        verbose_name_plural = 'Candidates'
        indexes = [
            models.Index(fields=['registration_number']),
            models.Index(fields=['registration_category']),
            models.Index(fields=['status']),
            models.Index(fields=['verification_status']),
            models.Index(fields=['assessment_center']),
            models.Index(fields=['occupation']),
            models.Index(fields=['entry_year', 'intake']),
        ]
    
    def __str__(self):
        return f"{self.registration_number} - {self.full_name}"

    def clean(self):
        super().clean()
        if not self.date_of_birth:
            return

        today = date.today()

        if self.date_of_birth > today:
            raise ValidationError({'date_of_birth': 'Date of birth cannot be in the future.'})

        def shift_years(d, years):
            try:
                return d.replace(year=d.year - years)
            except ValueError:
                return d.replace(year=d.year - years, month=2, day=28)

        min_dob = shift_years(today, 100)
        max_dob = shift_years(today, 12)

        if self.date_of_birth < min_dob:
            raise ValidationError({'date_of_birth': 'Candidate cannot be older than 100 years.'})
        if self.date_of_birth > max_dob:
            raise ValidationError({'date_of_birth': 'Candidate must be at least 12 years old.'})
    
    def is_modular(self):
        """Check if candidate is registered as Modular"""
        return self.registration_category == 'modular'
    
    def is_formal(self):
        """Check if candidate is registered as Formal"""
        return self.registration_category == 'formal'
    
    def is_workers_pas(self):
        """Check if candidate is registered as Worker's PAS"""
        return self.registration_category == 'workers_pas'
    
    def get_age(self):
        """Calculate candidate's age"""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def has_outstanding_balance(self):
        """Check if candidate has outstanding fees"""
        return self.fees_balance > 0
    
    def is_verified(self):
        """Check if candidate is verified"""
        return self.verification_status == 'verified'
    
    def is_declined(self):
        """Check if candidate is declined"""
        return self.verification_status == 'declined'
    
    def get_registration_category_code(self):
        """Get registration category code for registration number"""
        category_codes = {
            'modular': 'M',
            'formal': 'F',
            'workers_pas': 'W'
        }
        return category_codes.get(self.registration_category, 'F')
    
    def get_nationality_code(self):
        """Get nationality code for registration number"""
        # U for Ugandan, X for other nationalities
        # Use candidate_country (ISO code) if available, fallback to nationality
        if self.candidate_country:
            return 'U' if str(self.candidate_country) == 'UG' else 'X'
        elif self.nationality and self.nationality.lower() in ['uganda', 'ugandan']:
            return 'U'
        else:
            return 'X'
    
    def generate_registration_number(self):
        """
        Generate registration number in format:
        UVT218/U/25/M/MVM/F/016
        Format: center_no/nationality/year/intake/occ_code/reg_category/unique_no
        """
        if not all([self.assessment_center, self.entry_year, self.intake, 
                   self.occupation, self.registration_category]):
            return None
        
        # Get center number (e.g., UVT218)
        center_no = self.assessment_center.center_number if self.assessment_center else 'UVT000'
        
        # Get nationality code (U for Ugandan, R for Refugee)
        nationality_code = self.get_nationality_code()
        
        # Get year (last 2 digits)
        year_code = str(self.entry_year)[-2:]
        
        # Get intake (M, J, S, D)
        intake_code = self.intake
        
        # Get occupation code
        occ_code = self.occupation.occ_code if self.occupation else 'XXX'
        
        # Get registration category code (M, F, W)
        reg_category_code = self.get_registration_category_code()
        
        # Get unique number in assessment center for this year/intake
        # Count existing candidates in same center, year, intake
        from django.db.models import Max
        existing_candidates = Candidate.objects.filter(
            assessment_center=self.assessment_center,
            entry_year=self.entry_year,
            intake=self.intake
        ).exclude(pk=self.pk if self.pk else None)
        
        # Extract unique numbers from existing registration numbers
        max_unique_no = 0
        for candidate in existing_candidates:
            if candidate.registration_number:
                try:
                    # Extract the last part (unique number)
                    parts = candidate.registration_number.split('/')
                    if len(parts) >= 6:
                        unique_no = int(parts[-1])
                        max_unique_no = max(max_unique_no, unique_no)
                except (ValueError, IndexError):
                    continue
        
        # Increment for new candidate
        unique_no = str(max_unique_no + 1).zfill(3)
        
        # Construct registration number
        reg_number = f"{center_no}/{nationality_code}/{year_code}/{intake_code}/{occ_code}/{reg_category_code}/{unique_no}"
        
        return reg_number
    
    def generate_payment_code(self):
        """
        Generate payment code in format: IUV00225000001
        Format: I (Informal) + UV + center_no (3 digits) + year (2 digits) + candidate_id (7 digits with leading zeros)
        
        Example: UVT002/U/25/M/HD/F/0001 -> IUV00225000001
        - I: Informal system
        - UV: All centers start with UV
        - 002: Center number (from UVT002)
        - 25: Entry year (last 2 digits)
        - 0000001: Candidate ID with leading zeros (7 digits total)
        """
        if not all([self.assessment_center, self.entry_year, self.pk]):
            return None
        
        # Extract center number (e.g., UVT002 -> 002)
        center_no = self.assessment_center.center_number if self.assessment_center else 'UVT000'
        # Extract the numeric part after 'UVT'
        center_digits = center_no.replace('UVT', '').zfill(3)
        
        # Get year (last 2 digits)
        year_code = str(self.entry_year)[-2:]
        
        # Get candidate ID with leading zeros (7 digits)
        candidate_id = str(self.pk).zfill(7)
        
        # Construct payment code: I + UV + center_no + year + candidate_id
        payment_code = f"IUV{center_digits}{year_code}{candidate_id}"
        
        return payment_code
    
    def clean(self):
        """Validate candidate data"""
        from django.core.exceptions import ValidationError
        
        # Validate refugee number if is_refugee is True
        if self.is_refugee and not self.refugee_number:
            raise ValidationError({
                'refugee_number': 'Refugee number is required for refugees'
            })
        
        # Validate disability specification if has_disability is True
        if self.has_disability and not self.nature_of_disability:
            raise ValidationError({
                'nature_of_disability': 'Nature of disability must be specified'
            })
        
        # Validate modular module count for modular candidates
        if self.registration_category == 'modular':
            if self.modular_module_count and self.modular_module_count not in [1, 2]:
                raise ValidationError({
                    'modular_module_count': 'Modular candidates can only have 1 or 2 modules'
                })
        
        # Validate assessment center branch belongs to assessment center
        if self.assessment_center_branch and self.assessment_center:
            if self.assessment_center_branch.assessment_center != self.assessment_center:
                raise ValidationError({
                    'assessment_center_branch': 'Selected branch does not belong to the selected assessment center'
                })


class CandidateEnrollment(models.Model):
    """
    Model for managing candidate enrollments in assessment series
    """
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='enrollments')
    assessment_series = models.ForeignKey('assessment_series.AssessmentSeries', on_delete=models.CASCADE, related_name='enrollments')
    occupation_level = models.ForeignKey(
        'occupations.OccupationLevel', 
        on_delete=models.CASCADE, 
        related_name='enrollments',
        null=True,
        blank=True,
        help_text="Level for formal/modular candidates. Null for Worker's PAS (they select papers from any level)"
    )
    
    # Billing information
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Total Amount (UGX)'
    )
    
    is_active = models.BooleanField(default=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-enrolled_at']
        verbose_name = 'Candidate Enrollment'
        verbose_name_plural = 'Candidate Enrollments'
        # Remove unique_together since Workers PAS can have multiple enrollments per series
        # Uniqueness will be enforced in the view logic
    
    def __str__(self):
        level_name = self.occupation_level.level_name if self.occupation_level else "Worker's PAS"
        return f"{self.candidate.full_name} - {self.assessment_series.name} - {level_name}"


class EnrollmentModule(models.Model):
    """
    Model for tracking modules selected in an enrollment (for modular and workers_pas)
    """
    enrollment = models.ForeignKey(CandidateEnrollment, on_delete=models.CASCADE, related_name='modules')
    module = models.ForeignKey('occupations.OccupationModule', on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['module__module_code']
        verbose_name = 'Enrollment Module'
        verbose_name_plural = 'Enrollment Modules'
        unique_together = ['enrollment', 'module']
    
    def __str__(self):
        return f"{self.enrollment.candidate.full_name} - {self.module.module_code}"


class EnrollmentPaper(models.Model):
    """
    Model for tracking papers selected in an enrollment (for workers_pas)
    """
    enrollment = models.ForeignKey(CandidateEnrollment, on_delete=models.CASCADE, related_name='papers')
    paper = models.ForeignKey('occupations.OccupationPaper', on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['paper__paper_code']
        verbose_name = 'Enrollment Paper'
        verbose_name_plural = 'Enrollment Papers'
        unique_together = ['enrollment', 'paper']
    
    def __str__(self):
        return f"{self.enrollment.candidate.full_name} - {self.paper.paper_code}"


class CandidateActivity(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='activities')
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidate_activities'
    )
    action = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    details = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['candidate', 'created_at']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f"{self.candidate_id} - {self.action}"
