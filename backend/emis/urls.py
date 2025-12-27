"""
URL configuration for emis project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/users/', include('users.urls')),
    path('api/candidates/', include('candidates.urls')),
    path('api/occupations/', include('occupations.urls')),
    path('api/assessment-centers/', include('assessment_centers.urls')),
    path('api/assessment-series/', include('assessment_series.urls')),
    path('api/results/', include('results.urls')),
    path('api/awards/', include('awards.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/complaints/', include('complaints.urls')),
    path('api/statistics/', include('stats.urls')),
    path('api/configurations/', include('configurations.urls')),
    path('api/dit-migration/', include('dit_migration.urls')),
    path('api/fees/', include('fees.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "EMIS Administration"
admin.site.site_title = "EMIS Admin Portal"
admin.site.index_title = "Welcome to EMIS Administration"
