from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'staff', views.StaffViewSet, basename='staff')
router.register(r'support-staff', views.SupportStaffViewSet, basename='support-staff')
router.register(r'center-representatives', views.CenterRepresentativeViewSet, basename='center-representative')

urlpatterns = [
    # Auth endpoints
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('', include(router.urls)),
]