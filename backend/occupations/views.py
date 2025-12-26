from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Sector, Occupation, OccupationLevel, OccupationModule, OccupationPaper, ModuleLWA
from .serializers import (
    SectorSerializer,
    OccupationSerializer, OccupationCreateSerializer, OccupationListSerializer,
    OccupationLevelSerializer, OccupationLevelCreateSerializer,
    OccupationModuleSerializer, OccupationModuleCreateSerializer,
    OccupationPaperSerializer, OccupationPaperCreateSerializer,
    ModuleLWASerializer
)
from .views_lwa import ModuleLWAViewSet


class SectorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Sector model
    """
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow unauthenticated access
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    
    @action(detail=True, methods=['get'])
    def occupations(self, request, pk=None):
        """Get all occupations for a specific sector"""
        sector = self.get_object()
        occupations = sector.occupations.all()
        serializer = OccupationListSerializer(occupations, many=True)
        return Response({
            'sector_id': sector.id,
            'sector_name': sector.name,
            'occupations_count': occupations.count(),
            'occupations': serializer.data
        })


class OccupationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Occupation model
    """
    queryset = Occupation.objects.select_related('sector').prefetch_related('levels').all()
    serializer_class = OccupationSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow unauthenticated access
    filterset_fields = ['occ_category', 'has_modular', 'is_active', 'sector']
    search_fields = ['occ_code', 'occ_name', 'sector__name']
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return OccupationCreateSerializer
        elif self.action == 'list':
            return OccupationListSerializer
        return OccupationSerializer
    
    @action(detail=True, methods=['get'])
    def levels(self, request, pk=None):
        """Get all levels for a specific occupation"""
        occupation = self.get_object()
        levels = occupation.levels.all()
        serializer = OccupationLevelSerializer(levels, many=True)
        return Response({
            'occupation_id': occupation.id,
            'occ_code': occupation.occ_code,
            'occ_name': occupation.occ_name,
            'levels_count': levels.count(),
            'levels': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get occupations by category"""
        category = request.query_params.get('category', None)
        if category:
            occupations = self.queryset.filter(occ_category=category)
            serializer = self.get_serializer(occupations, many=True)
            return Response(serializer.data)
        return Response({'error': 'Category parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def formal(self, request):
        """Get all formal occupations"""
        occupations = self.queryset.filter(occ_category='formal')
        serializer = self.get_serializer(occupations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def workers_pas(self, request):
        """Get all Worker's PAS occupations"""
        occupations = self.queryset.filter(occ_category='workers_pas')
        serializer = self.get_serializer(occupations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def with_modular(self, request):
        """Get all occupations with modular registration"""
        occupations = self.queryset.filter(has_modular=True)
        serializer = self.get_serializer(occupations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_sector(self, request):
        """Get occupations by sector"""
        sector = request.query_params.get('sector', None)
        if sector:
            occupations = self.queryset.filter(sector__icontains=sector)
            serializer = self.get_serializer(occupations, many=True)
            return Response(serializer.data)
        return Response({'error': 'Sector parameter is required'}, status=status.HTTP_400_BAD_REQUEST)


class OccupationLevelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for OccupationLevel model
    """
    queryset = OccupationLevel.objects.select_related('occupation').all()
    serializer_class = OccupationLevelSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow unauthenticated access
    filterset_fields = ['occupation', 'structure_type', 'is_active']
    search_fields = ['level_name', 'occupation__occ_code', 'occupation__occ_name']
    
    def get_serializer_class(self):
        """Use different serializer for create action"""
        if self.action == 'create':
            return OccupationLevelCreateSerializer
        return OccupationLevelSerializer
    
    @action(detail=False, methods=['get'])
    def by_occupation(self, request):
        """Get all levels for a specific occupation"""
        occupation_id = request.query_params.get('occupation_id', None)
        if occupation_id:
            levels = self.queryset.filter(occupation_id=occupation_id)
            serializer = self.get_serializer(levels, many=True)
            return Response(serializer.data)
        return Response({'error': 'occupation_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_structure_type(self, request):
        """Get levels by structure type (modules or papers)"""
        structure_type = request.query_params.get('structure_type', None)
        if structure_type:
            levels = self.queryset.filter(structure_type=structure_type)
            serializer = self.get_serializer(levels, many=True)
            return Response(serializer.data)
        return Response({'error': 'structure_type parameter is required'}, status=status.HTTP_400_BAD_REQUEST)


class OccupationModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for OccupationModule model
    """
    queryset = OccupationModule.objects.select_related('occupation', 'level').all()
    serializer_class = OccupationModuleSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['occupation', 'level', 'is_active']
    search_fields = ['module_code', 'module_name', 'occupation__occ_code', 'occupation__occ_name']
    
    def get_serializer_class(self):
        """Use different serializer for create action"""
        if self.action == 'create':
            return OccupationModuleCreateSerializer
        return OccupationModuleSerializer
    
    @action(detail=False, methods=['get'], url_path='by-occupation')
    def by_occupation(self, request):
        """Get all modules for a specific occupation"""
        occupation_id = request.query_params.get('occupation', None) or request.query_params.get('occupation_id', None)
        if occupation_id:
            modules = self.queryset.filter(occupation_id=occupation_id)
            serializer = self.get_serializer(modules, many=True)
            return Response({'results': serializer.data})
        return Response({'error': 'occupation parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_level(self, request):
        """Get all modules for a specific level"""
        level_id = request.query_params.get('level_id', None)
        if level_id:
            modules = self.queryset.filter(level_id=level_id)
            serializer = self.get_serializer(modules, many=True)
            return Response(serializer.data)
        return Response({'error': 'level_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def levels_by_occupation(self, request):
        """Get available levels for a specific occupation (for dropdown filtering)"""
        occupation_id = request.query_params.get('occupation_id', None)
        if occupation_id:
            levels = OccupationLevel.objects.filter(occupation_id=occupation_id)
            serializer = OccupationLevelSerializer(levels, many=True)
            return Response(serializer.data)
        return Response({'error': 'occupation_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)


class OccupationPaperViewSet(viewsets.ModelViewSet):
    """
    ViewSet for OccupationPaper model
    """
    queryset = OccupationPaper.objects.select_related('occupation', 'level').all()
    serializer_class = OccupationPaperSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['occupation', 'level', 'paper_type', 'is_active']
    search_fields = ['paper_code', 'paper_name', 'occupation__occ_code', 'occupation__occ_name']
    
    def get_serializer_class(self):
        """Use different serializer for create action"""
        if self.action == 'create':
            return OccupationPaperCreateSerializer
        return OccupationPaperSerializer
    
    @action(detail=False, methods=['get'], url_path='by-occupation')
    def by_occupation(self, request):
        """Get all papers for a specific occupation"""
        occupation_id = request.query_params.get('occupation', None) or request.query_params.get('occupation_id', None)
        if occupation_id:
            papers = self.queryset.filter(occupation_id=occupation_id)
            serializer = self.get_serializer(papers, many=True)
            return Response({'results': serializer.data})
        return Response({'error': 'occupation parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_level(self, request):
        """Get all papers for a specific level"""
        level_id = request.query_params.get('level_id', None)
        if level_id:
            papers = self.queryset.filter(level_id=level_id)
            serializer = self.get_serializer(papers, many=True)
            return Response(serializer.data)
        return Response({'error': 'level_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_paper_type(self, request):
        """Get papers by type (theory or practical)"""
        paper_type = request.query_params.get('paper_type', None)
        if paper_type:
            papers = self.queryset.filter(paper_type=paper_type)
            serializer = self.get_serializer(papers, many=True)
            return Response(serializer.data)
        return Response({'error': 'paper_type parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def levels_by_occupation(self, request):
        """Get available levels for a specific occupation (for dropdown filtering)"""
        occupation_id = request.query_params.get('occupation_id', None)
        if occupation_id:
            levels = OccupationLevel.objects.filter(occupation_id=occupation_id)
            serializer = OccupationLevelSerializer(levels, many=True)
            return Response(serializer.data)
        return Response({'error': 'occupation_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)