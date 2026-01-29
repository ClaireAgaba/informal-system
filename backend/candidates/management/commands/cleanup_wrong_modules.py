"""
Management command to cleanup wrong modules from modular candidate enrollments.

This script identifies and removes enrollment modules that don't belong to the
candidate's occupation. For example, if a candidate is enrolled in "Motorcycle Mechanic"
but has modules from "Tailor" occupation, those wrong modules will be removed.

Usage:
    # Dry run (preview what would be deleted without making changes)
    python manage.py cleanup_wrong_modules --dry-run
    
    # Actually perform the cleanup
    python manage.py cleanup_wrong_modules
    
    # Verbose output with details
    python manage.py cleanup_wrong_modules --dry-run --verbose
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from candidates.models import Candidate, CandidateEnrollment, EnrollmentModule


class Command(BaseCommand):
    help = 'Remove enrollment modules that do not belong to the candidate\'s occupation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without actually deleting anything',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information for each candidate',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN MODE - No changes will be made ===\n'))
        else:
            self.stdout.write(self.style.WARNING('=== LIVE MODE - Changes will be saved ===\n'))
        
        # Get all modular candidates with active enrollments that have modules
        modular_enrollments = CandidateEnrollment.objects.filter(
            candidate__registration_category='modular',
            is_active=True,
            modules__isnull=False
        ).select_related(
            'candidate',
            'candidate__occupation',
        ).prefetch_related(
            'modules',
            'modules__module',
            'modules__module__occupation'
        ).distinct()
        
        total_enrollments = modular_enrollments.count()
        self.stdout.write(f'Found {total_enrollments} modular enrollments with modules\n')
        
        stats = {
            'enrollments_checked': 0,
            'enrollments_affected': 0,
            'modules_removed': 0,
            'modules_kept': 0,
            'candidates_affected': set(),
        }
        
        wrong_modules_to_delete = []
        
        for enrollment in modular_enrollments:
            candidate = enrollment.candidate
            candidate_occupation = candidate.occupation
            
            if not candidate_occupation:
                self.stdout.write(self.style.WARNING(
                    f'  SKIP: Candidate {candidate.full_name} (ID: {candidate.id}) has no occupation set'
                ))
                continue
            
            stats['enrollments_checked'] += 1
            
            enrollment_modules = list(enrollment.modules.all())
            wrong_modules = []
            correct_modules = []
            
            for em in enrollment_modules:
                module = em.module
                module_occupation = module.occupation
                
                if module_occupation.id != candidate_occupation.id:
                    wrong_modules.append(em)
                else:
                    correct_modules.append(em)
            
            if wrong_modules:
                stats['enrollments_affected'] += 1
                stats['modules_removed'] += len(wrong_modules)
                stats['modules_kept'] += len(correct_modules)
                stats['candidates_affected'].add(candidate.id)
                wrong_modules_to_delete.extend(wrong_modules)
                
                if verbose or dry_run:
                    self.stdout.write(self.style.NOTICE(
                        f'\nCandidate: {candidate.full_name} (ID: {candidate.id})'
                    ))
                    self.stdout.write(f'  Registration: {candidate.registration_number or "N/A"}')
                    self.stdout.write(f'  Occupation: {candidate_occupation.occ_name}')
                    self.stdout.write(self.style.SUCCESS(
                        f'  Correct modules ({len(correct_modules)}): ' + 
                        ', '.join([em.module.module_code for em in correct_modules]) if correct_modules else '  Correct modules: None'
                    ))
                    self.stdout.write(self.style.ERROR(
                        f'  WRONG modules to remove ({len(wrong_modules)}): ' +
                        ', '.join([f'{em.module.module_code} (belongs to {em.module.occupation.occ_name})' for em in wrong_modules])
                    ))
            else:
                stats['modules_kept'] += len(correct_modules)
                if verbose:
                    self.stdout.write(self.style.SUCCESS(
                        f'  OK: {candidate.full_name} - All {len(correct_modules)} modules are correct'
                    ))
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.NOTICE('SUMMARY'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Enrollments checked: {stats["enrollments_checked"]}')
        self.stdout.write(f'Enrollments affected: {stats["enrollments_affected"]}')
        self.stdout.write(f'Candidates affected: {len(stats["candidates_affected"])}')
        self.stdout.write(self.style.ERROR(f'Modules to be REMOVED: {stats["modules_removed"]}'))
        self.stdout.write(self.style.SUCCESS(f'Modules to be KEPT: {stats["modules_kept"]}'))
        
        if not dry_run and wrong_modules_to_delete:
            self.stdout.write('\n' + self.style.WARNING('Deleting wrong modules...'))
            
            try:
                with transaction.atomic():
                    deleted_count = 0
                    for em in wrong_modules_to_delete:
                        em.delete()
                        deleted_count += 1
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'\nSuccessfully deleted {deleted_count} wrong enrollment modules'
                    ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\nError during deletion: {str(e)}'))
                raise
        elif dry_run and wrong_modules_to_delete:
            self.stdout.write(self.style.WARNING(
                f'\nDRY RUN: Would have deleted {len(wrong_modules_to_delete)} enrollment modules'
            ))
            self.stdout.write(self.style.NOTICE(
                'Run without --dry-run to actually perform the cleanup'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('\nNo wrong modules found. Database is clean!'))
