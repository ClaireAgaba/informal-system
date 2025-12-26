from django.urls import path, include
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

# Register viewsets here when ready
# router.register(r'reports', ReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]
