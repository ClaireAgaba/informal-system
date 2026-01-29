from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CandidateViewSet, delete_enrollment_view, bulk_de_enroll_view, clear_candidate_data, bulk_clear_candidate_data, change_candidate_series, bulk_change_candidate_series, change_candidate_center, change_candidate_occupation, bulk_change_candidate_occupation, change_candidate_registration_category, bulk_change_candidate_registration_category, candidate_login, candidate_portal_data, enrollment_list_view, bulk_change_enrollment_series, bulk_de_enroll_by_enrollment, bulk_clear_enrollment_data
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
    
    # Enrollment list endpoint
    path('enrollments/', enrollment_list_view, name='enrollment-list'),
    path('enrollments/bulk-change-series/', bulk_change_enrollment_series, name='bulk-change-enrollment-series'),
    path('enrollments/bulk-de-enroll/', bulk_de_enroll_by_enrollment, name='bulk-de-enroll-by-enrollment'),
    path('enrollments/bulk-clear-data/', bulk_clear_enrollment_data, name='bulk-clear-enrollment-data'),
    
    # De-enrollment endpoints (must come before router.urls)
    path('enrollments/<int:enrollment_id>/', delete_enrollment_view, name='delete-enrollment'),
    path('bulk-de-enroll/', bulk_de_enroll_view, name='bulk-de-enroll'),
    path('bulk-clear-data/', bulk_clear_candidate_data, name='bulk-clear-candidate-data'),
    path('bulk-change-occupation/', bulk_change_candidate_occupation, name='bulk-change-candidate-occupation'),
    path('bulk-change-registration-category/', bulk_change_candidate_registration_category, name='bulk-change-candidate-registration-category'),
    path('bulk-change-series/', bulk_change_candidate_series, name='bulk-change-candidate-series'),
    path('<int:candidate_id>/clear-data/', clear_candidate_data, name='clear-candidate-data'),
    path('<int:candidate_id>/change-series/', change_candidate_series, name='change-candidate-series'),
    path('<int:candidate_id>/change-center/', change_candidate_center, name='change-candidate-center'),
    path('<int:candidate_id>/change-occupation/', change_candidate_occupation, name='change-candidate-occupation'),
    path('<int:candidate_id>/change-registration-category/', change_candidate_registration_category, name='change-candidate-registration-category'),
    
    path('', include(router.urls)),
    
    # SchoolPay Integration Endpoints
    path('payments/schoolpay/check-balance/', schoolpay_check_balance, name='schoolpay-check-balance'),
    path('payments/schoolpay/callback/', schoolpay_payment_callback, name='schoolpay-callback'),
    path('payments/schoolpay/test/', schoolpay_test_connection, name='schoolpay-test'),
]
