from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ModularResultViewSet, FormalResultViewSet, WorkersPasResultViewSet

router = DefaultRouter()

# Register modular results viewset
router.register(r'modular', ModularResultViewSet, basename='modular-result')

# Register formal results viewset
router.register(r'formal', FormalResultViewSet, basename='formal-result')

# Register workers pas results viewset
router.register(r'workers-pas', WorkersPasResultViewSet, basename='workers-pas-result')

urlpatterns = [
    path('', include(router.urls)),
]
