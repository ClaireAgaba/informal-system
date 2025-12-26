from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ModuleLWA
from .serializers import ModuleLWASerializer


class ModuleLWAViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Module LWAs
    """
    queryset = ModuleLWA.objects.select_related('module').all()
    serializer_class = ModuleLWASerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['module']
    search_fields = ['lwa_name', 'module__module_code', 'module__module_name']
    
    @action(detail=False, methods=['get'], url_path='by-module')
    def by_module(self, request):
        """Get all LWAs for a specific module"""
        module_id = request.query_params.get('module', None) or request.query_params.get('module_id', None)
        if module_id:
            lwas = self.queryset.filter(module_id=module_id)
            serializer = self.get_serializer(lwas, many=True)
            return Response({'results': serializer.data})
        return Response({'error': 'module parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
