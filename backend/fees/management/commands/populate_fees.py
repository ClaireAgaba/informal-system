from django.core.management.base import BaseCommand
from django.db.models import Sum, Count
from candidates.models import Candidate
from fees.models import CandidateFee, CenterFee
from assessment_centers.models import AssessmentCenter
from assessment_series.models import AssessmentSeries


class Command(BaseCommand):
    help = 'Populate candidate and center fees from existing candidates'

    def handle(self, *args, **options):
        self.stdout.write('Populating candidate fees...')
        
        # Populate Candidate Fees
        created_count = 0
        updated_count = 0
        
        # Get all candidate enrollments
        from candidates.models import CandidateEnrollment
        
        enrollments = CandidateEnrollment.objects.filter(
            is_active=True
        ).select_related('candidate', 'candidate__occupation', 'assessment_series', 'candidate__assessment_center')
        
        for enrollment in enrollments:
            candidate = enrollment.candidate
            
            # Determine total amount
            total_amount = enrollment.total_amount or 0
            
            if total_amount == 0:
                continue
            
            # Generate payment code
            payment_code = f"{candidate.registration_number}-{enrollment.assessment_series.id}"
            
            # Determine payment info
            amount_paid = candidate.payment_amount_cleared or 0
            payment_status = 'not_paid'
            attempt_status = 'no_attempt'
            payment_date = None
            
            if candidate.payment_cleared_date:
                payment_date = candidate.payment_cleared_date
                if amount_paid >= total_amount:
                    payment_status = 'successful'
                    attempt_status = 'successful'
                elif amount_paid > 0:
                    payment_status = 'pending_approval'
                    attempt_status = 'pending_approval'
            
            # Create or update
            fee, created = CandidateFee.objects.update_or_create(
                candidate=candidate,
                assessment_series=enrollment.assessment_series,
                defaults={
                    'payment_code': payment_code,
                    'total_amount': total_amount,
                    'amount_paid': amount_paid,
                    'amount_due': total_amount - amount_paid,
                    'payment_date': payment_date,
                    'payment_status': payment_status,
                    'attempt_status': attempt_status,
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Candidate Fees: Created {created_count}, Updated {updated_count}'
        ))
        
        # Populate Center Fees
        self.stdout.write('Populating center fees...')
        center_created = 0
        center_updated = 0
        
        series_list = AssessmentSeries.objects.all()
        centers = AssessmentCenter.objects.all()
        
        for series in series_list:
            for center in centers:
                candidate_fees = CandidateFee.objects.filter(
                    assessment_series=series,
                    candidate__assessment_center=center
                )
                
                if not candidate_fees.exists():
                    continue
                
                aggregated = candidate_fees.aggregate(
                    total_candidates=Count('id'),
                    total_amount=Sum('total_amount'),
                    amount_paid=Sum('amount_paid')
                )
                
                fee, created = CenterFee.objects.update_or_create(
                    assessment_series=series,
                    assessment_center=center,
                    defaults={
                        'total_candidates': aggregated['total_candidates'] or 0,
                        'total_amount': aggregated['total_amount'] or 0,
                        'amount_paid': aggregated['amount_paid'] or 0,
                        'amount_due': (aggregated['total_amount'] or 0) - (aggregated['amount_paid'] or 0),
                    }
                )
                
                if created:
                    center_created += 1
                else:
                    center_updated += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Center Fees: Created {center_created}, Updated {center_updated}'
        ))
        self.stdout.write(self.style.SUCCESS('Done!'))
