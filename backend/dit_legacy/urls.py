from django.urls import path

from . import views

urlpatterns = [
    path('search/', views.search, name='dit_legacy_search'),
    path('person/<str:person_id>/', views.person_detail, name='dit_legacy_person_detail'),
    path('person/<str:person_id>/photo/', views.person_photo, name='dit_legacy_person_photo'),
    path('person/<str:person_id>/results/', views.person_results, name='dit_legacy_person_results'),
]
