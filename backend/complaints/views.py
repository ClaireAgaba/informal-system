from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Complaint, ComplaintCategory, ComplaintAttachment
from .serializers import (
    ComplaintListSerializer,
    ComplaintDetailSerializer,
    ComplaintCreateSerializer,
    ComplaintUpdateSerializer,
    ComplaintCategorySerializer,
    ComplaintAttachmentSerializer
)


class ComplaintCategoryViewSet(viewsets.ModelViewSet):
    queryset = ComplaintCategory.objects.filter(is_active=True)
    serializer_class = ComplaintCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class ComplaintViewSet(viewsets.ModelViewSet):
    queryset = Complaint.objects.select_related(
        'category', 'exam_center', 'exam_series', 'program',
        'helpdesk_team', 'created_by'
    ).prefetch_related('attachments')
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category', 'exam_center', 'exam_series', 'program', 'helpdesk_team']
    search_fields = ['ticket_number', 'issue_description', 'exam_center__name', 'program__name']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ComplaintListSerializer
        elif self.action == 'create':
            return ComplaintCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ComplaintUpdateSerializer
        return ComplaintDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter by user role
        if user.is_authenticated:
            # Center representatives can only see complaints from their center
            if user.user_type == 'center_representative' and hasattr(user, 'center_rep_profile'):
                center_rep = user.center_rep_profile
                queryset = queryset.filter(exam_center=center_rep.assessment_center)
            # Regular users can only see their own complaints
            elif not user.is_staff:
                queryset = queryset.filter(created_by=user)
        
        return queryset

    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign complaint to helpdesk team member"""
        complaint = self.get_object()
        helpdesk_user_id = request.data.get('helpdesk_team')
        
        if not helpdesk_user_id:
            return Response(
                {'error': 'helpdesk_team is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from users.models import User
            helpdesk_user = User.objects.get(id=helpdesk_user_id, is_staff=True)
            complaint.helpdesk_team = helpdesk_user
            complaint.status = 'in_progress'
            complaint.save()
            
            serializer = self.get_serializer(complaint)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid helpdesk team member'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update complaint status"""
        complaint = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Complaint.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        complaint.status = new_status
        complaint.save()
        
        serializer = self.get_serializer(complaint)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_response(self, request, pk=None):
        """Add team response to complaint"""
        complaint = self.get_object()
        response_text = request.data.get('team_response')
        
        if not response_text:
            return Response(
                {'error': 'team_response is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        complaint.team_response = response_text
        complaint.save()
        
        serializer = self.get_serializer(complaint)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get complaint statistics"""
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'new': queryset.filter(status='new').count(),
            'in_progress': queryset.filter(status='in_progress').count(),
            'done': queryset.filter(status='done').count(),
            'cancelled': queryset.filter(status='cancelled').count(),
        }
        
        return Response(stats)


class ComplaintAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ComplaintAttachment.objects.all()
    serializer_class = ComplaintAttachmentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
