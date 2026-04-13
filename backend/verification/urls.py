from django.urls import path

from . import views

urlpatterns = [
    path('', views.verify, name='verify'),
    path('<str:source>/<str:person_id>/', views.verify_detail, name='verify_detail'),
]
