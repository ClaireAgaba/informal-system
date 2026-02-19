from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'regions', views.RegionViewSet, basename='region')
router.register(r'districts', views.DistrictViewSet, basename='district')
router.register(r'villages', views.VillageViewSet, basename='village')
router.register(r'nature-of-disabilities', views.NatureOfDisabilityViewSet, basename='nature-of-disability')
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'center-representatives', views.CenterRepresentativeViewSet, basename='center-representative')
router.register(r'reprint-reasons', views.ReprintReasonViewSet, basename='reprint-reason')

urlpatterns = [
    path('', include(router.urls)),
]
