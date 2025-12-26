from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssessmentSeriesViewSet

router = DefaultRouter()
router.register(r'series', AssessmentSeriesViewSet, basename='series')

urlpatterns = [
    path('', include(router.urls)),
]
