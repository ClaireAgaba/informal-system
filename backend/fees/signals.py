from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, Count
from candidates.models import CandidateEnrollment, Candidate
from .models import CandidateFee, CenterFee


@receiver(post_save, sender=CandidateEnrollment)
def create_or_update_candidate_fee(sender, instance, created, **kwargs):
    """Automatically create or update candidate fee when enrollment is saved"""
    if not instance.is_active:
        return
    
    candidate = instance.candidate
    total_amount = instance.total_amount or 0
    
    if total_amount == 0:
        return
    
    # Generate payment code
    payment_code = f"{candidate.registration_number}-{instance.assessment_series.id}"
    
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
    
    # Create or update candidate fee
    CandidateFee.objects.update_or_create(
        candidate=candidate,
        assessment_series=instance.assessment_series,
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
    
    # Update center fee
    update_center_fee(instance.assessment_series, candidate.assessment_center)


@receiver(post_save, sender=Candidate)
def update_candidate_fee_on_payment(sender, instance, created, **kwargs):
    """Update candidate fee when payment is cleared"""
    if created:
        return
    
    # Update all fees for this candidate
    fees = CandidateFee.objects.filter(candidate=instance)
    
    for fee in fees:
        amount_paid = instance.payment_amount_cleared or 0
        payment_status = 'not_paid'
        attempt_status = 'no_attempt'
        payment_date = None
        
        if instance.payment_cleared_date:
            payment_date = instance.payment_cleared_date
            if amount_paid >= fee.total_amount:
                payment_status = 'successful'
                attempt_status = 'successful'
            elif amount_paid > 0:
                payment_status = 'pending_approval'
                attempt_status = 'pending_approval'
        
        fee.amount_paid = amount_paid
        fee.amount_due = fee.total_amount - amount_paid
        fee.payment_date = payment_date
        fee.payment_status = payment_status
        fee.attempt_status = attempt_status
        fee.save()
        
        # Update center fee
        update_center_fee(fee.assessment_series, instance.assessment_center)


@receiver(post_delete, sender=CandidateEnrollment)
def delete_candidate_fee(sender, instance, **kwargs):
    """Delete candidate fee when enrollment is deleted"""
    CandidateFee.objects.filter(
        candidate=instance.candidate,
        assessment_series=instance.assessment_series
    ).delete()
    
    # Update center fee
    if instance.candidate.assessment_center:
        update_center_fee(instance.assessment_series, instance.candidate.assessment_center)


def update_center_fee(assessment_series, assessment_center):
    """Update center fee by aggregating candidate fees"""
    if not assessment_center:
        return
    
    # Aggregate candidate fees for this center and series
    candidate_fees = CandidateFee.objects.filter(
        assessment_series=assessment_series,
        candidate__assessment_center=assessment_center
    )
    
    if not candidate_fees.exists():
        # Delete center fee if no candidates
        CenterFee.objects.filter(
            assessment_series=assessment_series,
            assessment_center=assessment_center
        ).delete()
        return
    
    aggregated = candidate_fees.aggregate(
        total_candidates=Count('id'),
        total_amount=Sum('total_amount'),
        amount_paid=Sum('amount_paid')
    )
    
    # Create or update center fee
    CenterFee.objects.update_or_create(
        assessment_series=assessment_series,
        assessment_center=assessment_center,
        defaults={
            'total_candidates': aggregated['total_candidates'] or 0,
            'total_amount': aggregated['total_amount'] or 0,
            'amount_paid': aggregated['amount_paid'] or 0,
            'amount_due': (aggregated['total_amount'] or 0) - (aggregated['amount_paid'] or 0),
        }
    )
