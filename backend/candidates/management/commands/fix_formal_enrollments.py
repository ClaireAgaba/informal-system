from django.core.management.base import BaseCommand
from candidates.models import CandidateEnrollment, EnrollmentModule, EnrollmentPaper, Candidate


class Command(BaseCommand):
    help = 'Fix formal candidate enrollments by adding all modules/papers for their level'

    def handle(self, *args, **options):
        # Get all formal candidate enrollments
        formal_enrollments = CandidateEnrollment.objects.filter(
            candidate__registration_category='formal'
        ).select_related('occupation_level')

        fixed_count = 0
        for enrollment in formal_enrollments:
            level = enrollment.occupation_level
            
            if level.structure_type == 'modules':
                # Check if enrollment has modules
                if not enrollment.modules.exists():
                    # Add all modules for this level
                    all_modules = level.modules.all()
                    for module in all_modules:
                        EnrollmentModule.objects.get_or_create(
                            enrollment=enrollment,
                            module=module
                        )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Added {all_modules.count()} modules to enrollment {enrollment.id}'
                        )
                    )
                    fixed_count += 1
                    
            elif level.structure_type == 'papers':
                # Check if enrollment has papers
                if not enrollment.papers.exists():
                    # Add all papers for this level
                    all_papers = level.papers.all()
                    for paper in all_papers:
                        EnrollmentPaper.objects.get_or_create(
                            enrollment=enrollment,
                            paper=paper
                        )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Added {all_papers.count()} papers to enrollment {enrollment.id}'
                        )
                    )
                    fixed_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully fixed {fixed_count} formal enrollments'
            )
        )
