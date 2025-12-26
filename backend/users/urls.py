from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'staff', views.StaffViewSet, basename='staff')
router.register(r'support-staff', views.SupportStaffViewSet, basename='support-staff')

urlpatterns = [
    path('', include(router.urls)),
]