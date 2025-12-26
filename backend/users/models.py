from django.db import models
from django.contrib.auth.models import AbstractUser
from configurations.models import Department


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    """
    USER_TYPE_CHOICES = (
        ('staff', 'Staff'),
        ('support_staff', 'Support Staff'),
        ('candidate', 'Candidate'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='candidate')
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