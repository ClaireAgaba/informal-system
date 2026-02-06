from django.core.management.base import BaseCommand
from candidates.models import Candidate


class Command(BaseCommand):
    help = 'Migrate nationality CharField values to candidate_country CountryField'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Mapping from country names to ISO 3166-1 alpha-2 codes
        COUNTRY_NAME_TO_CODE = {
            # East Africa
            'Uganda': 'UG',
            'Kenya': 'KE',
            'Tanzania': 'TZ',
            'Rwanda': 'RW',
            'Burundi': 'BI',
            'South Sudan': 'SS',
            'DR Congo': 'CD',
            'Ethiopia': 'ET',
            'Somalia': 'SO',
            'Eritrea': 'ER',
            'Djibouti': 'DJ',
            'Sudan': 'SD',
            
            # Rest of Africa
            'Nigeria': 'NG',
            'Ghana': 'GH',
            'South Africa': 'ZA',
            'Zambia': 'ZM',
            'Zimbabwe': 'ZW',
            'Malawi': 'MW',
            'Mozambique': 'MZ',
            'Angola': 'AO',
            'Botswana': 'BW',
            'Namibia': 'NA',
            'Eswatini': 'SZ',
            'Lesotho': 'LS',
            'Madagascar': 'MG',
            'Mauritius': 'MU',
            'Seychelles': 'SC',
            'Comoros': 'KM',
            'Cameroon': 'CM',
            'Gabon': 'GA',
            'Congo': 'CG',
            'Central African Republic': 'CF',
            'Chad': 'TD',
            'Niger': 'NE',
            'Mali': 'ML',
            'Burkina Faso': 'BF',
            'Senegal': 'SN',
            'Gambia': 'GM',
            'Guinea-Bissau': 'GW',
            'Guinea': 'GN',
            'Sierra Leone': 'SL',
            'Liberia': 'LR',
            "Côte d'Ivoire": 'CI',
            'Ivory Coast': 'CI',
            'Togo': 'TG',
            'Benin': 'BJ',
            'Mauritania': 'MR',
            'Egypt': 'EG',
            'Libya': 'LY',
            'Tunisia': 'TN',
            'Algeria': 'DZ',
            'Morocco': 'MA',
            
            # International
            'United States': 'US',
            'United Kingdom': 'GB',
            'India': 'IN',
            'China': 'CN',
            'Pakistan': 'PK',
            'Bangladesh': 'BD',
        }
        
        # Get all candidates
        candidates = Candidate.objects.all()
        total_candidates = candidates.count()
        updated_count = 0
        skipped_count = 0
        unmapped_nationalities = {}
        
        self.stdout.write(f"\nProcessing {total_candidates} candidates...")
        
        for candidate in candidates:
            if candidate.nationality:
                country_code = COUNTRY_NAME_TO_CODE.get(candidate.nationality)
                
                if country_code:
                    if dry_run:
                        self.stdout.write(
                            f"Would update: {candidate.registration_number or candidate.id} - "
                            f"{candidate.nationality} → {country_code}"
                        )
                    else:
                        candidate.candidate_country = country_code
                        candidate.save(update_fields=['candidate_country'])
                    updated_count += 1
                else:
                    # Track unmapped nationalities
                    if candidate.nationality not in unmapped_nationalities:
                        unmapped_nationalities[candidate.nationality] = 0
                    unmapped_nationalities[candidate.nationality] += 1
                    skipped_count += 1
            else:
                skipped_count += 1
        
        # Summary
        self.stdout.write("\n" + "="*60)
        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN - No changes made"))
        
        self.stdout.write(self.style.SUCCESS(f"\n✓ Total candidates: {total_candidates}"))
        self.stdout.write(self.style.SUCCESS(f"✓ Would update: {updated_count}" if dry_run else f"✓ Updated: {updated_count}"))
        
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f"⚠ Skipped: {skipped_count}"))
        
        # Log unmapped nationalities
        if unmapped_nationalities:
            self.stdout.write(self.style.WARNING(f"\n⚠ Found {len(unmapped_nationalities)} unmapped nationality values:"))
            for nationality, count in sorted(unmapped_nationalities.items()):
                self.stdout.write(f"  - {nationality}: {count} candidate(s)")
            self.stdout.write(self.style.WARNING("\nThese candidates will keep default value 'UG' (Uganda)"))
        
        self.stdout.write("\n" + "="*60 + "\n")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Run without --dry-run to apply changes"))
