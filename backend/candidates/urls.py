from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CandidateViewSet
from .views_payment import (
    schoolpay_check_balance,
    schoolpay_payment_callback,
    schoolpay_test_connection
)

router = DefaultRouter()
router.register(r'', CandidateViewSet, basename='candidate')

urlpatterns = [
    path('', include(router.urls)),
    
    # SchoolPay Integration Endpoints
    path('payments/schoolpay/check-balance/', schoolpay_check_balance, name='schoolpay-check-balance'),
    path('payments/schoolpay/callback/', schoolpay_payment_callback, name='schoolpay-callback'),
    path('payments/schoolpay/test/', schoolpay_test_connection, name='schoolpay-test'),
]
