from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CandidateViewSet, delete_enrollment_view, candidate_login, candidate_portal_data
from .views_payment import (
    schoolpay_check_balance,
    schoolpay_payment_callback,
    schoolpay_test_connection
)

router = DefaultRouter()
router.register(r'', CandidateViewSet, basename='candidate')

urlpatterns = [
    # Candidate Portal Endpoints (must come before router.urls)
    path('candidate-login/', candidate_login, name='candidate-login'),
    path('candidate-portal/<path:registration_number>/', candidate_portal_data, name='candidate-portal-data'),
    
    # De-enrollment endpoint (must come before router.urls)
    path('enrollments/<int:enrollment_id>/', delete_enrollment_view, name='delete-enrollment'),
    
    path('', include(router.urls)),
    
    # SchoolPay Integration Endpoints
    path('payments/schoolpay/check-balance/', schoolpay_check_balance, name='schoolpay-check-balance'),
    path('payments/schoolpay/callback/', schoolpay_payment_callback, name='schoolpay-callback'),
    path('payments/schoolpay/test/', schoolpay_test_connection, name='schoolpay-test'),
]
