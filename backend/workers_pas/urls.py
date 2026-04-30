from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    WorkersPasOccupationListView, WorkersPasSeriesListView,
    WorkersPasCandidateListView, WorkersPasGenerateView,
    WorkersPasBulkGenerateView, WorkersPasBookViewSet,
)


router = DefaultRouter()
router.register(r'books', WorkersPasBookViewSet, basename='workers-pas-book')


urlpatterns = [
    path('occupations/', WorkersPasOccupationListView.as_view(),
         name='workers-pas-occupations'),
    path('series/', WorkersPasSeriesListView.as_view(),
         name='workers-pas-series'),
    path('candidates/', WorkersPasCandidateListView.as_view(),
         name='workers-pas-candidates'),
    path('generate/', WorkersPasGenerateView.as_view(),
         name='workers-pas-generate'),
    path('bulk-generate/', WorkersPasBulkGenerateView.as_view(),
         name='workers-pas-bulk-generate'),
]

urlpatterns += router.urls
