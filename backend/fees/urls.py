from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CandidateFeeViewSet, CenterFeeViewSet

router = DefaultRouter()
router.register(r'candidate-fees', CandidateFeeViewSet, basename='candidate-fee')
router.register(r'center-fees', CenterFeeViewSet, basename='center-fee')

urlpatterns = [
    path('', include(router.urls)),
]
