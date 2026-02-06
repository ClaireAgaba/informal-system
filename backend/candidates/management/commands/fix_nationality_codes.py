from django.core.management.base import BaseCommand
from candidates.models import Candidate


class Command(BaseCommand):
    help = 'Update 2-letter nationality codes to full country names'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dryrun',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dryrun = options.get('dryrun', False)
        # Mapping of 2-letter codes to full country names
        nationality_map = {
            'UG': 'Uganda',
            'KE': 'Kenya',
            'TZ': 'Tanzania',
            'RW': 'Rwanda',
            'BI': 'Burundi',
            'SS': 'South Sudan',
            'CD': 'DR Congo',
            'ET': 'Ethiopia',
            'SO': 'Somalia',
            'ER': 'Eritrea',
            'DJ': 'Djibouti',
            'SD': 'Sudan',
            'NG': 'Nigeria',
            'GH': 'Ghana',
            'ZA': 'South Africa',
            'ZM': 'Zambia',
            'ZW': 'Zimbabwe',
            'MW': 'Malawi',
            'MZ': 'Mozambique',
            'AO': 'Angola',
            'BW': 'Botswana',
            'NA': 'Namibia',
            'SZ': 'Eswatini',
            'LS': 'Lesotho',
            'MG': 'Madagascar',
            'MU': 'Mauritius',
            'SC': 'Seychelles',
            'KM': 'Comoros',
            'CM': 'Cameroon',
            'GA': 'Gabon',
            'CG': 'Congo',
            'CF': 'Central African Republic',
            'TD': 'Chad',
            'NE': 'Niger',
            'ML': 'Mali',
            'BF': 'Burkina Faso',
            'SN': 'Senegal',
            'GM': 'Gambia',
            'GW': 'Guinea-Bissau',
            'GN': 'Guinea',
            'SL': 'Sierra Leone',
            'LR': 'Liberia',
            'CI': "Côte d'Ivoire",
            'TG': 'Togo',
            'BJ': 'Benin',
            'MR': 'Mauritania',
            'EG': 'Egypt',
            'LY': 'Libya',
            'TN': 'Tunisia',
            'DZ': 'Algeria',
            'MA': 'Morocco',
            'US': 'United States',
            'GB': 'United Kingdom',
            'IN': 'India',
            'CN': 'China',
            'PK': 'Pakistan',
            'BD': 'Bangladesh',
        }

        total_updated = 0
        
        if dryrun:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))
        self.stdout.write(self.style.NOTICE('Starting nationality code update...'))
        self.stdout.write('')

        for code, full_name in nationality_map.items():
            # Find candidates with this 2-letter code (case insensitive)
            candidates = Candidate.objects.filter(nationality__iexact=code)
            count = candidates.count()
            
            if count > 0:
                if not dryrun:
                    candidates.update(nationality=full_name)
                self.stdout.write(f'  {"Would update" if dryrun else "Updated"} {count} candidates: {code} -> {full_name}')
                total_updated += count

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Done! {"Would update" if dryrun else "Updated"} {total_updated} candidates total.'))
        
        # Show current nationality distribution
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('Current nationality distribution:'))
        from django.db.models import Count
        nationalities = Candidate.objects.values('nationality').annotate(
            count=Count('id')
        ).order_by('-count')[:20]
        
        for nat in nationalities:
            self.stdout.write(f"  {nat['nationality'] or 'NULL'}: {nat['count']}")
