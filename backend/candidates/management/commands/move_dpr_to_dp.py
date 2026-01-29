"""
Management command to move candidates from occupation DPR to DP.

This fixes an error where a duplicate occupation was created. The script will:
1. Move all candidates from occupation code 'DPR' to occupation code 'DP'
2. Update registration numbers to reflect the new occupation code (DPR -> DP)
3. NOT touch enrollments or results

Usage:
    # Dry run (preview what would be changed)
    python manage.py move_dpr_to_dp --dry-run
    
    # Actually perform the migration
    python manage.py move_dpr_to_dp
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from candidates.models import Candidate
from occupations.models import Occupation


class Command(BaseCommand):
    help = 'Move candidates from occupation DPR to DP and update registration numbers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without actually making them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN MODE - No changes will be made ===\n'))
        else:
            self.stdout.write(self.style.WARNING('=== LIVE MODE - Changes will be saved ===\n'))
        
        # Find both occupations
        try:
            dpr_occupation = Occupation.objects.get(occ_code='DPR')
            self.stdout.write(f'Found source occupation: {dpr_occupation.occ_name} (DPR) - ID: {dpr_occupation.id}')
        except Occupation.DoesNotExist:
            self.stdout.write(self.style.ERROR('ERROR: Occupation with code "DPR" not found!'))
            return
        
        try:
            dp_occupation = Occupation.objects.get(occ_code='DP')
            self.stdout.write(f'Found target occupation: {dp_occupation.occ_name} (DP) - ID: {dp_occupation.id}')
        except Occupation.DoesNotExist:
            self.stdout.write(self.style.ERROR('ERROR: Occupation with code "DP" not found!'))
            return
        
        # Find all candidates with DPR occupation
        candidates = Candidate.objects.filter(occupation=dpr_occupation)
        total_candidates = candidates.count()
        
        self.stdout.write(f'\nFound {total_candidates} candidates with occupation DPR\n')
        
        if total_candidates == 0:
            self.stdout.write(self.style.SUCCESS('No candidates to migrate.'))
            return
        
        stats = {
            'occupation_updated': 0,
            'regno_updated': 0,
            'regno_unchanged': 0,
            'errors': [],
        }
        
        # Sample of candidates to show
        sample_changes = []
        
        for candidate in candidates:
            old_regno = candidate.registration_number
            new_regno = None
            
            # Update registration number if it exists and contains DPR
            if old_regno and '/DPR/' in old_regno:
                new_regno = old_regno.replace('/DPR/', '/DP/')
                stats['regno_updated'] += 1
            elif old_regno:
                stats['regno_unchanged'] += 1
            
            # Collect sample for display (first 10)
            if len(sample_changes) < 10:
                sample_changes.append({
                    'id': candidate.id,
                    'name': candidate.full_name,
                    'old_regno': old_regno,
                    'new_regno': new_regno or old_regno,
                })
            
            stats['occupation_updated'] += 1
            
            if not dry_run:
                try:
                    candidate.occupation = dp_occupation
                    if new_regno:
                        candidate.registration_number = new_regno
                    candidate.save(update_fields=['occupation', 'registration_number'])
                except Exception as e:
                    stats['errors'].append({
                        'candidate_id': candidate.id,
                        'name': candidate.full_name,
                        'error': str(e)
                    })
        
        # Show sample changes
        self.stdout.write('\n--- Sample of changes (first 10) ---')
        for change in sample_changes:
            self.stdout.write(f'  {change["name"]} (ID: {change["id"]})')
            if change['old_regno'] != change['new_regno']:
                self.stdout.write(f'    Reg No: {change["old_regno"]} -> {change["new_regno"]}')
            else:
                self.stdout.write(f'    Reg No: {change["old_regno"]} (unchanged)')
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.NOTICE('SUMMARY'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'Total candidates: {total_candidates}')
        self.stdout.write(f'Occupation changed (DPR -> DP): {stats["occupation_updated"]}')
        self.stdout.write(f'Registration numbers updated: {stats["regno_updated"]}')
        self.stdout.write(f'Registration numbers unchanged: {stats["regno_unchanged"]}')
        
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f'\nErrors: {len(stats["errors"])}'))
            for err in stats['errors'][:5]:
                self.stdout.write(self.style.ERROR(f'  - {err["name"]}: {err["error"]}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\nDRY RUN: Would have migrated {total_candidates} candidates from DPR to DP'
            ))
            self.stdout.write(self.style.NOTICE(
                'Run without --dry-run to actually perform the migration'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\nSuccessfully migrated {stats["occupation_updated"]} candidates from DPR to DP'
            ))
