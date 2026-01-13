from django.db import models
from django.contrib.auth.models import AbstractUser
from configurations.models import Department
from django.contrib.auth.hashers import make_password


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    """
    USER_TYPE_CHOICES = (
        ('staff', 'Staff'),
        ('support_staff', 'Support Staff'),
        ('center_representative', 'Center Representative'),
        ('candidate', 'Candidate'),
    )
    
    user_type = models.CharField(max_length=25, choices=USER_TYPE_CHOICES, default='candidate')
    phone_number = models.CharField(max_length=15, blank=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class Staff(models.Model):
    """
    Model for managing staff members
    """
    ACCOUNT_STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='staff_profile', null=True, blank=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    contact = models.CharField(max_length=15, verbose_name='Contact Number')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='staff_members')
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUS_CHOICES, default='active')
    
    # Additional fields
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Staff Member'
        verbose_name_plural = 'Staff Members'
    
    def __str__(self):
        return f"{self.full_name} - {self.department.name if self.department else 'No Department'}"
    
    def is_active(self):
        """Check if staff account is active"""
        return self.account_status == 'active'
    
    def get_accessible_modules(self):
        """Get list of modules this staff member can access based on department"""
        if self.department:
            return self.department.module_rights
        return []
    
    def save(self, *args, **kwargs):
        """Override save to auto-create user account"""
        if not self.user:
            # Create new user with email as username
            user = User.objects.create(
                username=self.email,
                email=self.email,
                first_name=self.full_name.split()[0] if self.full_name else '',
                last_name=' '.join(self.full_name.split()[1:]) if len(self.full_name.split()) > 1 else '',
                user_type='staff',
                phone_number=self.contact,
                is_staff=True,
                is_active=self.account_status == 'active'
            )
            # Set default password: uvtab@2025
            user.set_password('uvtab@2025')
            user.save()
            self.user = user
        else:
            # Update existing user
            self.user.email = self.email
            self.user.phone_number = self.contact
            self.user.first_name = self.full_name.split()[0] if self.full_name else ''
            self.user.last_name = ' '.join(self.full_name.split()[1:]) if len(self.full_name.split()) > 1 else ''
            self.user.is_active = self.account_status == 'active'
            self.user.save()
        
        super().save(*args, **kwargs)


class SupportStaff(models.Model):
    """
    Model for managing support staff members
    """
    ACCOUNT_STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='support_staff_profile', null=True, blank=True)
    full_name = models.CharField(max_length=200)
    contact = models.CharField(max_length=15, verbose_name='Contact Number')
    email = models.EmailField(unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='support_staff_members')
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUS_CHOICES, default='active')
    
    # Additional fields
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Support Staff Member'
        verbose_name_plural = 'Support Staff Members'
    
    def __str__(self):
        return f"{self.full_name} - {self.department.name if self.department else 'No Department'}"
    
    def is_active(self):
        """Check if support staff account is active"""
        return self.account_status == 'active'
    
    def get_accessible_modules(self):
        """Get list of modules this support staff member can access based on department"""
        if self.department:
            return self.department.module_rights
        return []
    
    def save(self, *args, **kwargs):
        """Override save to auto-create user account"""
        if not self.user:
            # Create new user with email as username
            user = User.objects.create(
                username=self.email,
                email=self.email,
                first_name=self.full_name.split()[0] if self.full_name else '',
                last_name=' '.join(self.full_name.split()[1:]) if len(self.full_name.split()) > 1 else '',
                user_type='support_staff',
                phone_number=self.contact,
                is_staff=False,
                is_active=self.account_status == 'active'
            )
            # Set default password: uvtab@2025
            user.set_password('uvtab@2025')
            user.save()
            self.user = user
        else:
            # Update existing user
            self.user.email = self.email
            self.user.phone_number = self.contact
            self.user.first_name = self.full_name.split()[0] if self.full_name else ''
            self.user.last_name = ' '.join(self.full_name.split()[1:]) if len(self.full_name.split()) > 1 else ''
            self.user.is_active = self.account_status == 'active'
            self.user.save()
        
        super().save(*args, **kwargs)


class CenterRepresentative(models.Model):
    """
    Model for managing Center Representatives
    """
    ACCOUNT_STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='center_rep_profile', null=True, blank=True)
    fullname = models.CharField(max_length=200, verbose_name='Full Name')
    contact = models.CharField(max_length=15, verbose_name='Contact Number')
    email = models.EmailField(unique=True, editable=False)  # Auto-generated, not editable
    assessment_center = models.ForeignKey(
        'assessment_centers.AssessmentCenter', 
        on_delete=models.CASCADE, 
        related_name='representatives'
    )
    assessment_center_branch = models.ForeignKey(
        'assessment_centers.CenterBranch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='representatives',
        verbose_name='Assessment Center Branch'
    )
    account_status = models.CharField(max_length=20, choices=ACCOUNT_STATUS_CHOICES, default='active')
    
    # Additional fields
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_center_reps')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Center Representative'
        verbose_name_plural = 'Center Representatives'
    
    def __str__(self):
        return f"{self.fullname} - {self.assessment_center.center_name if self.assessment_center else 'No Center'}"
    
    def is_active(self):
        """Check if center representative account is active"""
        return self.account_status == 'active'
    
    def save(self, *args, **kwargs):
        """Override save to auto-generate email and create user account"""
        # Generate email if not set (format: centerno@uvtab.go.ug or centerno-branchcode@uvtab.go.ug)
        if not self.email and self.assessment_center:
            center_no = self.assessment_center.center_number.lower()
            if self.assessment_center_branch:
                # Branch rep: include branch code suffix
                branch_code = self.assessment_center_branch.branch_code or ''
                branch_suffix = branch_code.split('-')[-1].lower() if branch_code else ''
                self.email = f"{center_no}-{branch_suffix}@uvtab.go.ug"
            else:
                # Main center rep
                self.email = f"{center_no}@uvtab.go.ug"
        
        # Create or update User account
        if not self.user:
            # Create new user with auto-generated credentials
            user = User.objects.create(
                username=self.email,
                email=self.email,
                first_name=self.fullname.split()[0] if self.fullname else '',
                last_name=' '.join(self.fullname.split()[1:]) if len(self.fullname.split()) > 1 else '',
                user_type='center_representative',
                phone_number=self.contact,
                is_staff=False,
                is_active=True
            )
            # Set default password: uvtab@2025
            user.set_password('uvtab@2025')
            user.save()
            self.user = user
        else:
            # Update existing user
            self.user.email = self.email
            self.user.phone_number = self.contact
            self.user.first_name = self.fullname.split()[0] if self.fullname else ''
            self.user.last_name = ' '.join(self.fullname.split()[1:]) if len(self.fullname.split()) > 1 else ''
            self.user.save()
        
        super().save(*args, **kwargs)