from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'sectors', views.SectorViewSet, basename='sector')
router.register(r'occupations', views.OccupationViewSet, basename='occupation')
router.register(r'levels', views.OccupationLevelViewSet, basename='occupation-level')
router.register(r'modules', views.OccupationModuleViewSet, basename='occupation-module')
router.register(r'papers', views.OccupationPaperViewSet, basename='occupation-paper')
router.register(r'module-lwas', views.ModuleLWAViewSet, basename='module-lwa')

urlpatterns = [
    path('', include(router.urls)),
]