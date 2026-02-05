from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AwardsViewSet

router = DefaultRouter()
router.register(r'', AwardsViewSet, basename='awards')

urlpatterns = [
    path('', include(router.urls)),
]
