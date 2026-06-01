"""
Management command to clean up orphaned and duplicate fee records.

Usage:
    python manage.py cleanup_fees              # Dry-run: shows what would be fixed
    python manage.py cleanup_fees --fix        # Actually delete/repair
    python manage.py cleanup_fees --fix -v 2   # Verbose output
"""
from django.core.management.base import BaseCommand
from django.db.models import Count

from candidates.models import CandidateEnrollment
from fees.models import CandidateFee, CenterFee
from fees.signals import update_center_fee


class Command(BaseCommand):
    help = 'Clean up orphaned and duplicate fee records, then recalculate center totals.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            default=False,
            help='Actually delete orphaned/duplicate fees. Without this flag, only a dry-run report is printed.',
        )

    def handle(self, *args, **options):
        fix = options['fix']
        verbosity = options['verbosity']

        self.stdout.write(self.style.NOTICE(
            f"{'🔧 FIX MODE' if fix else '👀 DRY-RUN MODE (use --fix to apply changes)'}"
        ))
        self.stdout.write('')

        # ──────────────────────────────────────────────────
        # 1. Orphaned fees — CandidateFee with no active enrollment
        # ──────────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('1. Orphaned fees (no active enrollment)'))

        all_fees = CandidateFee.objects.select_related(
            'candidate', 'assessment_series'
        ).all()

        orphaned = []
        for fee in all_fees:
            has_enrollment = CandidateEnrollment.objects.filter(
                candidate=fee.candidate,
                assessment_series=fee.assessment_series,
                is_active=True,
            ).exists()
            if not has_enrollment:
                orphaned.append(fee)

        if orphaned:
            self.stdout.write(self.style.WARNING(f'   Found {len(orphaned)} orphaned fee(s):'))
            for fee in orphaned:
                label = (
                    f'     • {fee.candidate.registration_number or fee.candidate_id} | '
                    f'Series: {fee.assessment_series.name} | '
                    f'Amount: {fee.total_amount} | '
                    f'Status: {fee.verification_status}'
                )
                if verbosity >= 2:
                    self.stdout.write(label)
            if fix:
                # Don't delete fees that accounts has already marked/approved
                deletable = [f for f in orphaned if f.verification_status == 'pending']
                locked = [f for f in orphaned if f.verification_status != 'pending']
                if deletable:
                    ids = [f.id for f in deletable]
                    CandidateFee.objects.filter(id__in=ids).delete()
                    self.stdout.write(self.style.SUCCESS(f'   ✓ Deleted {len(deletable)} orphaned fee(s)'))
                if locked:
                    self.stdout.write(self.style.WARNING(
                        f'   ⚠ Skipped {len(locked)} orphaned fee(s) with marked/approved status (manual review needed)'
                    ))
            else:
                self.stdout.write('   (no changes — dry run)')
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ No orphaned fees found'))

        self.stdout.write('')

        # ──────────────────────────────────────────────────
        # 2. Duplicate fees — multiple CandidateFee rows per (candidate, series)
        # ──────────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('2. Duplicate fees (same candidate + series)'))

        dupes = (
            CandidateFee.objects
            .values('candidate_id', 'assessment_series_id')
            .annotate(cnt=Count('id'))
            .filter(cnt__gt=1)
        )

        dupe_count = 0
        deleted_dupes = 0
        for dupe in dupes:
            dupe_count += 1
            fees = list(
                CandidateFee.objects.filter(
                    candidate_id=dupe['candidate_id'],
                    assessment_series_id=dupe['assessment_series_id'],
                ).order_by('-updated_at')
            )
            keep = fees[0]  # keep the most recently updated
            extras = fees[1:]

            if verbosity >= 2:
                self.stdout.write(
                    f'     • Candidate {dupe["candidate_id"]} / '
                    f'Series {dupe["assessment_series_id"]}: '
                    f'{len(fees)} rows — keeping id={keep.id}, removing {[f.id for f in extras]}'
                )

            if fix:
                # Only delete duplicates that are pending (not marked/approved)
                for extra in extras:
                    if extra.verification_status == 'pending':
                        extra.delete()
                        deleted_dupes += 1
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'     ⚠ Skipped duplicate id={extra.id} (status={extra.verification_status})'
                        ))

        if dupe_count:
            self.stdout.write(self.style.WARNING(f'   Found {dupe_count} candidate(s) with duplicate fees'))
            if fix:
                self.stdout.write(self.style.SUCCESS(f'   ✓ Deleted {deleted_dupes} duplicate fee(s)'))
            else:
                self.stdout.write('   (no changes — dry run)')
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ No duplicate fees found'))

        self.stdout.write('')

        # ──────────────────────────────────────────────────
        # 3. Recalculate all center fee totals
        # ──────────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('3. Recalculating center fee totals'))

        if fix:
            center_fees = CenterFee.objects.select_related(
                'assessment_series', 'assessment_center'
            ).all()
            recalculated = 0
            for cf in center_fees:
                update_center_fee(cf.assessment_series, cf.assessment_center)
                recalculated += 1

            # Also check for centers that have candidate fees but no CenterFee row
            from django.db.models import Q
            candidate_fee_combos = (
                CandidateFee.objects
                .values('assessment_series_id', 'candidate__assessment_center_id')
                .annotate(cnt=Count('id'))
            )
            for combo in candidate_fee_combos:
                series_id = combo['assessment_series_id']
                center_id = combo['candidate__assessment_center_id']
                if center_id and not CenterFee.objects.filter(
                    assessment_series_id=series_id,
                    assessment_center_id=center_id,
                ).exists():
                    from assessment_series.models import AssessmentSeries
                    from assessment_centers.models import AssessmentCenter
                    update_center_fee(
                        AssessmentSeries.objects.get(pk=series_id),
                        AssessmentCenter.objects.get(pk=center_id),
                    )
                    recalculated += 1

            self.stdout.write(self.style.SUCCESS(f'   ✓ Recalculated {recalculated} center fee(s)'))
        else:
            center_count = CenterFee.objects.count()
            self.stdout.write(f'   Would recalculate {center_count} center fee(s) (dry run)')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Done.'))
