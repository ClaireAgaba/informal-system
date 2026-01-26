from django.urls import path
from . import views
from .excel_export import export_series_excel

urlpatterns = [
    path('overall/', views.overall_statistics, name='overall-statistics'),
    path('candidates/by-gender/', views.candidates_by_gender, name='candidates-by-gender'),
    path('candidates/by-category/', views.candidates_by_category, name='candidates-by-category'),
    path('candidates/by-special-needs/', views.candidates_by_special_needs, name='candidates-by-special-needs'),
    
    # Assessment Series endpoints
    path('series/', views.assessment_series_list, name='assessment-series-list'),
    path('series/<int:series_id>/results/', views.assessment_series_results, name='assessment-series-results'),
    path('series/<int:series_id>/export-excel/', export_series_excel, name='export-series-excel'),
    
    # Special needs and refugee analytics
    path('special-needs/', views.special_needs_analytics, name='special-needs-analytics'),
]

