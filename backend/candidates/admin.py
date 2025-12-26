from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Candidate


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = [
        'registration_number', 'payment_code', 'full_name', 'get_occupation_code', 'registration_category',
        'intake', 'entry_year', 'assessment_center', 'verification_status', 
        'status', 'payment_cleared', 'created_at'
    ]
    
    list_filter = [
        'registration_category', 'intake', 'entry_year', 'verification_status',
        'status', 'payment_cleared', 'gender', 'is_refugee', 'has_disability',
        'assessment_center', 'occupation', 'created_at'
    ]
    
    search_fields = [
        'registration_number', 'payment_code', 'full_name', 'contact', 'refugee_number',
        'occupation__occ_code', 'occupation__occ_name', 'assessment_center__center_name'
    ]
    
    readonly_fields = [
        'registration_number', 'payment_code', 'created_at', 'updated_at', 'get_age_display',
        'verification_date', 'payment_cleared_date', 'created_by', 'updated_by'
    ]
    
    autocomplete_fields = [
        'district', 'village', 'nature_of_disability', 'assessment_center',
        'assessment_center_branch', 'occupation', 'verified_by', 'payment_cleared_by'
    ]
    
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Registration Information', {
            'fields': (
                'registration_number', 'payment_code', 'registration_category', 'status',
                'entry_year', 'intake'
            ),
            'description': 'Registration number and payment code are auto-generated based on center, year, intake, and occupation'
        }),
        ('Personal Information', {
            'fields': (
                'full_name', 'date_of_birth', 'get_age_display', 'gender',
                'nationality', 'is_refugee', 'refugee_number'
            )
        }),
        ('Contact & Location', {
            'fields': ('contact', 'district', 'village')
        }),
        ('Disability Information', {
            'fields': ('has_disability', 'nature_of_disability', 'disability_specification'),
            'classes': ('collapse',)
        }),
        ('Assessment Information', {
            'fields': (
                'assessment_center', 'assessment_center_branch', 'occupation',
                'preferred_assessment_language', 'start_date', 'finish_date', 'assessment_date'
            )
        }),
        ('Modular-Specific Information', {
            'fields': ('modular_module_count', 'modular_billing_amount'),
            'classes': ('collapse',),
            'description': 'Only applicable for Modular registration category'
        }),
        ('Document Uploads', {
            'fields': (
                'passport_photo', 'identification_document', 'qualification_document'
            ),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': (
                'verification_status', 'verification_date', 'verified_by', 'decline_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Payment Information', {
            'fields': (
                'fees_balance', 'payment_cleared', 'payment_cleared_date',
                'payment_cleared_by', 'payment_amount_cleared', 'payment_center_series_ref'
            ),
            'classes': ('collapse',)
        }),
        ('Portal Settings', {
            'fields': ('block_portal_results', 'enrollment_level', 'reg_number'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': (
                ('created_by', 'created_at'),
                ('updated_by', 'updated_at')
            ),
            'classes': ('collapse',),
            'description': 'Automatically tracked - Created by and Updated by are set automatically'
        }),
    )
    
    actions = [
        'verify_candidates', 'decline_candidates', 'mark_payment_cleared',
        'generate_registration_numbers', 'regenerate_registration_numbers',
        'generate_payment_codes',
        'activate_candidates', 'deactivate_candidates'
    ]
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related(
            'district', 'village', 'nature_of_disability', 'assessment_center',
            'assessment_center_branch', 'occupation', 'created_by', 'verified_by'
        )
    
    def get_occupation_code(self, obj):
        """Display occupation code"""
        if obj.occupation:
            return obj.occupation.occ_code
        return '-'
    get_occupation_code.short_description = 'Occupation Code'
    get_occupation_code.admin_order_field = 'occupation__occ_code'
    
    def get_age_display(self, obj):
        """Display candidate's age"""
        return f"{obj.get_age()} years"
    get_age_display.short_description = 'Age'
    
    def get_created_by_display(self, obj):
        """Display who created the candidate"""
        if obj.created_by:
            return obj.created_by.fullname
        return '-'
    get_created_by_display.short_description = 'Created By'
    
    def get_updated_by_display(self, obj):
        """Display who last updated the candidate"""
        if obj.updated_by:
            return obj.updated_by.fullname
        return '-'
    get_updated_by_display.short_description = 'Updated By'
    
    def save_model(self, request, obj, form, change):
        """Auto-generate registration number and track staff"""
        # Get staff member from current user
        staff_member = None
        if hasattr(request.user, 'staff'):
            staff_member = request.user.staff
        
        if not change:  # New candidate - set created_by
            obj.created_by = staff_member
        
        # Always update updated_by on any save
        obj.updated_by = staff_member
        
        # Generate registration number if not already set
        if not obj.registration_number:
            reg_number = obj.generate_registration_number()
            if reg_number:
                obj.registration_number = reg_number
        
        super().save_model(request, obj, form, change)
    
    # Admin Actions
    def verify_candidates(self, request, queryset):
        """Verify selected candidates"""
        staff = request.user.staff if hasattr(request.user, 'staff') else None
        updated = queryset.update(
            verification_status='verified',
            verification_date=timezone.now(),
            verified_by=staff
        )
        self.message_user(request, f'{updated} candidate(s) verified successfully.')
    verify_candidates.short_description = 'Verify selected candidates'
    
    def decline_candidates(self, request, queryset):
        """Decline selected candidates"""
        staff = request.user.staff if hasattr(request.user, 'staff') else None
        updated = queryset.update(
            verification_status='declined',
            verification_date=timezone.now(),
            verified_by=staff
        )
        self.message_user(request, f'{updated} candidate(s) declined.')
    decline_candidates.short_description = 'Decline selected candidates'
    
    def mark_payment_cleared(self, request, queryset):
        """Mark payment as cleared for selected candidates"""
        staff = request.user.staff if hasattr(request.user, 'staff') else None
        updated = queryset.update(
            payment_cleared=True,
            payment_cleared_date=timezone.now().date(),
            payment_cleared_by=staff
        )
        self.message_user(request, f'Payment cleared for {updated} candidate(s).')
    mark_payment_cleared.short_description = 'Mark payment as cleared'
    
    def generate_registration_numbers(self, request, queryset):
        """Generate registration numbers for candidates without one"""
        updated = 0
        for candidate in queryset:
            if not candidate.registration_number:
                reg_number = candidate.generate_registration_number()
                if reg_number:
                    candidate.registration_number = reg_number
                    candidate.save()
                    updated += 1
        self.message_user(request, f'Generated registration numbers for {updated} candidate(s).')
    generate_registration_numbers.short_description = 'Generate registration numbers'
    
    def regenerate_registration_numbers(self, request, queryset):
        """Regenerate registration numbers for selected candidates (fixes wrong formats)"""
        updated = 0
        errors = 0
        error_messages = []
        
        # Only regenerate for submitted candidates
        queryset = queryset.filter(is_submitted=True)
        
        for candidate in queryset:
            try:
                # Validate required fields
                if not all([
                    candidate.assessment_center,
                    candidate.occupation,
                    candidate.entry_year,
                    candidate.intake,
                    candidate.registration_category
                ]):
                    error_messages.append(f'{candidate.full_name}: Missing required fields')
                    errors += 1
                    continue
                
                # Build registration number components
                center_number = candidate.assessment_center.center_number
                nationality_code = 'U' if candidate.nationality == 'Uganda' else 'X'
                year_code = str(candidate.entry_year)[-2:]
                intake_code = candidate.intake
                occ_code = candidate.occupation.occ_code
                
                reg_cat_map = {
                    'modular': 'M',
                    'formal': 'F',
                    'workers_pas': 'I'
                }
                reg_cat_code = reg_cat_map.get(candidate.registration_category, 'M')
                
                # Get sequence number from existing registration number if possible
                if candidate.registration_number:
                    parts = candidate.registration_number.split('/')
                    try:
                        # Try to extract existing sequence number
                        seq_num = int(parts[-1])
                    except (ValueError, IndexError):
                        # If can't extract, find the next available sequence
                        last_candidate = Candidate.objects.filter(
                            assessment_center=candidate.assessment_center,
                            occupation=candidate.occupation,
                            is_submitted=True,
                            registration_number__isnull=False
                        ).exclude(id=candidate.id).order_by('-id').first()
                        
                        if last_candidate and last_candidate.registration_number:
                            parts = last_candidate.registration_number.split('/')
                            try:
                                seq_num = int(parts[-1]) + 1
                            except (ValueError, IndexError):
                                seq_num = 1
                        else:
                            seq_num = 1
                else:
                    # No existing registration number, assign next sequence
                    last_candidate = Candidate.objects.filter(
                        assessment_center=candidate.assessment_center,
                        occupation=candidate.occupation,
                        is_submitted=True,
                        registration_number__isnull=False
                    ).exclude(id=candidate.id).order_by('-id').first()
                    
                    if last_candidate and last_candidate.registration_number:
                        parts = last_candidate.registration_number.split('/')
                        try:
                            seq_num = int(parts[-1]) + 1
                        except (ValueError, IndexError):
                            seq_num = 1
                    else:
                        seq_num = 1
                
                # Generate new registration number
                new_reg_number = f'{center_number}/{nationality_code}/{year_code}/{intake_code}/{occ_code}/{reg_cat_code}/{seq_num:04d}'
                
                # Update candidate
                candidate.registration_number = new_reg_number
                candidate.save()
                updated += 1
                
            except Exception as e:
                error_messages.append(f'{candidate.full_name}: {str(e)}')
                errors += 1
        
        # Show results
        if updated > 0:
            self.message_user(request, f'Successfully regenerated registration numbers for {updated} candidate(s).', level='success')
        if errors > 0:
            self.message_user(request, f'Failed to regenerate {errors} candidate(s). Errors: {"; ".join(error_messages[:5])}', level='warning')
    
    regenerate_registration_numbers.short_description = 'Regenerate registration numbers (fix wrong formats)'
    
    def generate_payment_codes(self, request, queryset):
        """Generate payment codes for selected candidates who have registration numbers"""
        updated = 0
        skipped = 0
        errors = 0
        error_messages = []
        
        # Only process submitted candidates with registration numbers
        queryset = queryset.filter(is_submitted=True, registration_number__isnull=False)
        
        for candidate in queryset:
            try:
                # Skip if payment code already exists
                if candidate.payment_code:
                    skipped += 1
                    continue
                
                # Validate required fields for payment code generation
                if not all([candidate.assessment_center, candidate.entry_year, candidate.pk]):
                    error_messages.append(f'{candidate.full_name}: Missing required fields (center, year, or ID)')
                    errors += 1
                    continue
                
                # Generate payment code
                payment_code = candidate.generate_payment_code()
                
                if payment_code:
                    candidate.payment_code = payment_code
                    candidate.save()
                    updated += 1
                else:
                    error_messages.append(f'{candidate.full_name}: Failed to generate payment code')
                    errors += 1
                
            except Exception as e:
                error_messages.append(f'{candidate.full_name}: {str(e)}')
                errors += 1
        
        # Show results
        messages = []
        if updated > 0:
            messages.append(f'Successfully generated payment codes for {updated} candidate(s).')
        if skipped > 0:
            messages.append(f'Skipped {skipped} candidate(s) who already have payment codes.')
        if errors > 0:
            messages.append(f'Failed to generate payment codes for {errors} candidate(s). Errors: {"; ".join(error_messages[:5])}')
        
        for message in messages:
            level = 'success' if 'Successfully' in message else 'warning' if 'Failed' in message else 'info'
            self.message_user(request, message, level=level)
    
    generate_payment_codes.short_description = 'Generate Payment Code'
    
    def activate_candidates(self, request, queryset):
        """Activate selected candidates"""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} candidate(s) activated.')
    activate_candidates.short_description = 'Activate selected candidates'
    
    def deactivate_candidates(self, request, queryset):
        """Deactivate selected candidates"""
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} candidate(s) deactivated.')
    deactivate_candidates.short_description = 'Deactivate selected candidates'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter assessment center branch based on selected assessment center"""
        if db_field.name == "assessment_center_branch":
            # For add/change form, show branches with center info
            from assessment_centers.models import CenterBranch
            kwargs["queryset"] = CenterBranch.objects.select_related('assessment_center').all()
        
        if db_field.name == "village":
            # For add/change form, show villages with district info
            from configurations.models import Village
            kwargs["queryset"] = Village.objects.select_related('district').all()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
