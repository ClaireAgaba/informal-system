from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from candidates.models import Candidate

class Command(BaseCommand):   
    help = 'Fix incorrect registration numbers (nationality code and/or year mismatch)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=5,
            help='Number of days to look back for candidates'
        )
        parser.add_argument(
            '--wet-run',
            action='store_true',
            help='Actually execute the changes (default is dry-run)',
        )
        parser.add_argument(
            '--fix-year',
            action='store_true',
            help='Also fix candidates whose reg number year does not match entry_year',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = not options['wet_run']
        fix_year = options['fix_year']
        
        start_date = timezone.now() - timedelta(days=days)
        self.stdout.write(f"Checking candidates created after: {start_date}")
        self.stdout.write(f"Fix year mismatches: {fix_year}")
        
        candidates = Candidate.objects.filter(
            created_at__gte=start_date,
            registration_number__isnull=False,
        )

        if not fix_year:
            candidates = candidates.filter(registration_number__contains='/X/')
        
        self.stdout.write(f"Found {candidates.count()} candidates to check.")
        
        fixed_count = 0
        
        for candidate in candidates:
            needs_fix = False
            reasons = []
            
            # Check nationality code
            correct_nat_code = candidate.get_nationality_code()
            if correct_nat_code == 'U' and '/X/' in (candidate.registration_number or ''):
                needs_fix = True
                reasons.append(f"nationality: X -> U")
            
            # Check year mismatch
            if fix_year and candidate.registration_number and candidate.entry_year:
                parts = candidate.registration_number.split('/')
                if len(parts) >= 3:
                    reg_year = parts[2]
                    expected_year = str(candidate.entry_year)[-2:]
                    if reg_year != expected_year:
                        needs_fix = True
                        reasons.append(f"year: {reg_year} -> {expected_year}")
            
            if needs_fix:
                old_reg = candidate.registration_number
                new_reg = candidate.generate_registration_number()
                
                if new_reg and new_reg != old_reg:
                    self.stdout.write(f"Fixing: {old_reg} -> {new_reg}")
                    self.stdout.write(f"  Name: {candidate.full_name}, Reasons: {', '.join(reasons)}")
                    
                    if not dry_run:
                        candidate.registration_number = new_reg
                        candidate.save()
                        self.stdout.write(self.style.SUCCESS("  [SAVED]"))
                    else:
                        self.stdout.write(self.style.WARNING("  [DRY RUN - Not Saved]"))
                    
                    fixed_count += 1
            
        self.stdout.write(f"\nTotal fixed: {fixed_count} (Dry Run: {dry_run})")
