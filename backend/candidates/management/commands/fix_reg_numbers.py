from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from candidates.models import Candidate

class Command(BaseCommand):   
    help = 'Fix incorrect registration numbers with /X/ for Ugandan candidates'

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

    def handle(self, *args, **options):
        days = options['days']
        dry_run = not options['wet_run']
        
        start_date = timezone.now() - timedelta(days=days)
        self.stdout.write(f"Checking candidates created after: {start_date}")
        
        candidates = Candidate.objects.filter(
            created_at__gte=start_date,
            registration_number__contains='/X/'
        )
        
        self.stdout.write(f"Found {candidates.count()} potential candidates to fix.")
        
        fixed_count = 0
        
        for candidate in candidates:
            correct_code = candidate.get_nationality_code()
            
            if correct_code == 'U':
                old_reg = candidate.registration_number
                new_reg = candidate.generate_registration_number()
                
                if '/U/' in new_reg:
                    self.stdout.write(f"Fixing: {old_reg} -> {new_reg}")
                    self.stdout.write(f"  Name: {candidate.full_name}, Nationality: {candidate.nationality}")
                    
                    if not dry_run:
                        candidate.registration_number = new_reg
                        candidate.save()
                        self.stdout.write(self.style.SUCCESS("  [SAVED]"))
                    else:
                        self.stdout.write(self.style.WARNING("  [DRY RUN - Not Saved]"))
                    
                    fixed_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f"Skipping {old_reg}: Generated {new_reg} which still looks wrong."))
            
        self.stdout.write(f"\nTotal fixed: {fixed_count} (Dry Run: {dry_run})")
