from rest_framework import viewsets, permissions
from .models import Region, District, Village, NatureOfDisability, Department
from .serializers import (
    RegionSerializer, DistrictSerializer, VillageSerializer, 
    NatureOfDisabilitySerializer, DepartmentSerializer
)


class RegionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Region model
    """
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_active', 'name']
    search_fields = ['name', 'description']


class DistrictViewSet(viewsets.ModelViewSet):
    """
    ViewSet for District model
    """
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow unauthenticated access
    filterset_fields = ['region', 'is_active']
    search_fields = ['name']


class VillageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Village model
    """
    queryset = Village.objects.select_related('district').all()
    serializer_class = VillageSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow unauthenticated access
    filterset_fields = ['district', 'district__region', 'is_active']
    search_fields = ['name', 'district__name']


class NatureOfDisabilityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for NatureOfDisability model
    """
    queryset = NatureOfDisability.objects.all()
    serializer_class = NatureOfDisabilitySerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow unauthenticated access
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Department model
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow unauthenticated access
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']


