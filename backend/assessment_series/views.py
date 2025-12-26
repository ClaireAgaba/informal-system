from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AssessmentSeries
from .serializers import AssessmentSeriesSerializer


class AssessmentSeriesViewSet(viewsets.ModelViewSet):
    """ViewSet for AssessmentSeries model"""
    queryset = AssessmentSeries.objects.all()
    serializer_class = AssessmentSeriesSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow unauthenticated access
    
    @action(detail=True, methods=['post'])
    def set_current(self, request, pk=None):
        """Set this series as the current assessment series"""
        series = self.get_object()
        series.is_current = True
        series.save()
        serializer = self.get_serializer(series)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def release_results(self, request, pk=None):
        """Release results for this assessment series"""
        series = self.get_object()
        series.results_released = True
        series.save()
        serializer = self.get_serializer(series)
        return Response(serializer.data)
