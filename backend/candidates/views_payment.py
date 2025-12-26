"""
Payment Integration Views for SchoolPay
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from .models import Candidate, CandidateEnrollment
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])  # SchoolPay needs to access this without authentication
def schoolpay_check_balance(request):
    """
    API endpoint for SchoolPay to check candidate balance
    
    Request from SchoolPay:
    GET/POST /api/payments/schoolpay/check-balance/
    {
        "payment_code": "IUV00225000001"
    }
    
    Response to SchoolPay:
    {
        "success": true,
        "student_no": "IUV00225000001",
        "student_name": "John Doe",
        "school_name": "UBTEB - Informal System",
        "outstanding_balance": 80000.00,
        "currency": "UGX"
    }
    """
    # Get payment code from request
    if request.method == 'GET':
        payment_code = request.GET.get('payment_code')
    else:
        payment_code = request.data.get('payment_code')
    
    if not payment_code:
        return Response({
            'success': False,
            'error': 'Payment code is required',
            'message': 'Please provide a valid payment code'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find candidate by payment code
        candidate = Candidate.objects.get(payment_code=payment_code)
        
        # Calculate total billed amount from enrollments
        total_billed = candidate.enrollments.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Calculate outstanding balance (total billed - amount already paid)
        amount_paid = candidate.payment_amount_cleared or Decimal('0.00')
        outstanding_balance = total_billed - amount_paid
        
        # Ensure balance is not negative
        if outstanding_balance < 0:
            outstanding_balance = Decimal('0.00')
        
        # Get assessment center name
        center_name = candidate.assessment_center.center_name if candidate.assessment_center else 'UVTAB - Informal System'
        
        return Response({
            'success': True,
            'student_no': candidate.payment_code,
            'student_name': candidate.full_name,
            'registration_number': candidate.registration_number,
            'school_name': center_name,
            'outstanding_balance': float(outstanding_balance),
            'total_billed': float(total_billed),
            'amount_paid': float(amount_paid),
            'currency': 'UGX',
            'payment_cleared': candidate.payment_cleared
        }, status=status.HTTP_200_OK)
        
    except Candidate.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Candidate not found',
            'message': 'No candidate found with this payment code. Please contact your school.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error checking balance for payment code {payment_code}: {str(e)}")
        return Response({
            'success': False,
            'error': 'Server error',
            'message': 'An error occurred while checking balance. Please try again later.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])  # SchoolPay needs to access this without authentication
def schoolpay_payment_callback(request):
    """
    API endpoint for SchoolPay to notify us of successful payments
    
    IMPORTANT: Partial payments are NOT allowed. Payment amount must match total billed exactly.
    
    Request from SchoolPay:
    POST /api/candidates/payments/schoolpay/callback/
    {
        "payment_code": "IUV00225000001",
        "school_pay_reference": "37414523724",
        "amount": 80000.00,  # MUST match total billed amount exactly
        "payment_status": "Pending Approval",  # or "Not Paid"
        "attempt_status": "Successful",  # or "No Attempt"
        "payment_date": "2025-12-23T13:55:23",
        "phone_number": "256700000000",
        "channel": "MTN Mobile Money"
    }
    
    Response to SchoolPay (Success):
    {
        "success": true,
        "message": "Payment recorded successfully",
        "transaction_id": "37414523724"
    }
    
    Response to SchoolPay (Partial Payment Rejected):
    {
        "success": false,
        "error": "Partial payment not allowed",
        "message": "Payment amount must be exactly UGX 80000.0. Partial payments are not accepted."
    }
    """
    try:
        # Extract payment data
        payment_code = request.data.get('payment_code')
        school_pay_reference = request.data.get('school_pay_reference')
        amount = request.data.get('amount')
        payment_status = request.data.get('payment_status')
        attempt_status = request.data.get('attempt_status')
        payment_date = request.data.get('payment_date')
        phone_number = request.data.get('phone_number')
        channel = request.data.get('channel')
        
        # Validate required fields
        if not all([payment_code, school_pay_reference, amount]):
            return Response({
                'success': False,
                'error': 'Missing required fields',
                'message': 'payment_code, school_pay_reference, and amount are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find candidate
        candidate = Candidate.objects.get(payment_code=payment_code)
        
        # Log the payment attempt
        logger.info(f"Payment callback received for {payment_code}: "
                   f"Reference={school_pay_reference}, Amount={amount}, Status={payment_status}")
        
        # Calculate total billed amount
        total_billed = candidate.enrollments.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Validate that payment amount matches total billed (no partial payments allowed)
        payment_amount = Decimal(str(amount))
        if payment_amount != total_billed:
            return Response({
                'success': False,
                'error': 'Partial payment not allowed',
                'message': f'Payment amount must be exactly UGX {float(total_billed)}. Partial payments are not accepted.',
                'amount_paid': float(payment_amount),
                'required_amount': float(total_billed)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Only mark as cleared if payment was successful and amount is correct
        if attempt_status == 'Successful' and payment_status != 'Not Paid':
            # Update candidate payment information
            candidate.payment_center_series_ref = school_pay_reference
            candidate.payment_amount_cleared = payment_amount
            candidate.payment_cleared = True
            
            from django.utils import timezone
            candidate.payment_cleared_date = timezone.now()
            
            candidate.save()
            
            return Response({
                'success': True,
                'message': 'Payment recorded successfully',
                'transaction_id': school_pay_reference,
                'candidate_name': candidate.full_name,
                'amount_paid': float(amount),
                'total_paid': float(candidate.payment_amount_cleared),
                'payment_cleared': candidate.payment_cleared
            }, status=status.HTTP_200_OK)
        else:
            # Payment failed or pending
            return Response({
                'success': True,
                'message': 'Payment status recorded',
                'transaction_id': school_pay_reference,
                'note': f'Payment status: {payment_status}, Attempt: {attempt_status}'
            }, status=status.HTTP_200_OK)
            
    except Candidate.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Candidate not found',
            'message': 'No candidate found with this payment code'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error processing payment callback: {str(e)}")
        return Response({
            'success': False,
            'error': 'Server error',
            'message': 'An error occurred while processing payment'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def schoolpay_test_connection(request):
    """
    Test endpoint to verify SchoolPay can reach our API
    """
    return Response({
        'success': True,
        'message': 'Connection successful',
        'system': 'UVTAB Informal System',
        'version': '1.0'
    }, status=status.HTTP_200_OK)
