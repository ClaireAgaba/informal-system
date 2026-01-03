from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ComplaintViewSet, ComplaintCategoryViewSet, ComplaintAttachmentViewSet

router = DefaultRouter()
router.register(r'complaints', ComplaintViewSet, basename='complaint')
router.register(r'categories', ComplaintCategoryViewSet, basename='complaint-category')
router.register(r'attachments', ComplaintAttachmentViewSet, basename='complaint-attachment')

urlpatterns = [
    path('', include(router.urls)),
]
