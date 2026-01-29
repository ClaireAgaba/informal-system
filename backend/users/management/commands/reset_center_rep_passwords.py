from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
    help = 'Reset passwords for all center representative users to a specified password'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            type=str,
            default='uvtab',
            help='Password to set (default: uvtab)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        password = options['password']
        dry_run = options['dry_run']

        center_reps = User.objects.filter(user_type='center_representative')
        count = center_reps.count()

        if count == 0:
            self.stdout.write(self.style.WARNING('No center representative users found.'))
            return

        self.stdout.write(f'Found {count} center representative user(s)')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] Would reset passwords for:'))
            for user in center_reps:
                self.stdout.write(f'  - {user.email} ({user.username})')
            self.stdout.write(self.style.WARNING(f'\n[DRY RUN] No changes made.'))
            return

        reset_count = 0
        for user in center_reps:
            user.set_password(password)
            user.save()
            reset_count += 1
            self.stdout.write(f'  Reset: {user.email}')

        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully reset passwords for {reset_count} center representative(s) to "{password}"'
        ))
