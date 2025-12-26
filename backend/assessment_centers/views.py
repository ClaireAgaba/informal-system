from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import AssessmentCenter, CenterBranch
from .serializers import (
    AssessmentCenterSerializer, AssessmentCenterCreateSerializer, AssessmentCenterListSerializer,
    CenterBranchSerializer, CenterBranchCreateSerializer
)


class AssessmentCenterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for AssessmentCenter model
    """
    queryset = AssessmentCenter.objects.select_related('district', 'village').prefetch_related('branches').all()
    serializer_class = AssessmentCenterSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow unauthenticated access
    filterset_fields = ['assessment_category', 'has_branches', 'is_active', 'district', 'village']
    search_fields = ['center_number', 'center_name', 'contact_1', 'contact_2']
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return AssessmentCenterCreateSerializer
        elif self.action == 'list':
            return AssessmentCenterListSerializer
        return AssessmentCenterSerializer
    
    @action(detail=True, methods=['get'])
    def branches(self, request, pk=None):
        """Get all branches for a specific center"""
        center = self.get_object()
        branches = center.branches.all()
        serializer = CenterBranchSerializer(branches, many=True)
        return Response({
            'center_id': center.id,
            'center_number': center.center_number,
            'center_name': center.center_name,
            'branches_count': branches.count(),
            'branches': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get centers grouped by assessment category"""
        category = request.query_params.get('category', None)
        if category:
            centers = self.queryset.filter(assessment_category=category)
            serializer = self.get_serializer(centers, many=True)
            return Response(serializer.data)
        return Response({'error': 'Category parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def with_branches(self, request):
        """Get all centers that have branches"""
        centers = self.queryset.filter(has_branches=True)
        serializer = self.get_serializer(centers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_district(self, request):
        """Get centers by district"""
        district_id = request.query_params.get('district_id', None)
        if district_id:
            centers = self.queryset.filter(district_id=district_id)
            serializer = self.get_serializer(centers, many=True)
            return Response(serializer.data)
        return Response({'error': 'district_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)


class CenterBranchViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CenterBranch model
    """
    queryset = CenterBranch.objects.select_related('assessment_center', 'district', 'village').all()
    serializer_class = CenterBranchSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow unauthenticated access
    filterset_fields = ['assessment_center', 'district', 'village', 'is_active']
    search_fields = ['branch_code', 'assessment_center__center_name', 'assessment_center__center_number']
    
    def get_serializer_class(self):
        """Use different serializer for create action"""
        if self.action == 'create':
            return CenterBranchCreateSerializer
        return CenterBranchSerializer
    
    @action(detail=False, methods=['get'])
    def by_center(self, request):
        """Get all branches for a specific center"""
        center_id = request.query_params.get('center_id', None)
        if center_id:
            branches = self.queryset.filter(assessment_center_id=center_id)
            serializer = self.get_serializer(branches, many=True)
            return Response(serializer.data)
        return Response({'error': 'center_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)