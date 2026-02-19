from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'centers', views.AssessmentCenterViewSet, basename='assessment-center')
router.register(r'branches', views.CenterBranchViewSet, basename='center-branch')
router.register(r'representative-persons', views.CenterRepresentativePersonViewSet, basename='representative-person')

urlpatterns = [
    path('', include(router.urls)),
]