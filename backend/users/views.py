from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import User, Staff, SupportStaff
from .serializers import (
    UserSerializer, StaffSerializer, StaffCreateSerializer,
    SupportStaffSerializer, SupportStaffCreateSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['user_type', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']


class StaffViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Staff model
    """
    queryset = Staff.objects.select_related('department', 'user').all()
    serializer_class = StaffSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow unauthenticated access
    filterset_fields = ['account_status', 'department', 'department__name']
    search_fields = ['full_name', 'email', 'contact']
    
    def get_serializer_class(self):
        """Use different serializer for create action"""
        if self.action == 'create':
            return StaffCreateSerializer
        return StaffSerializer
    
    @action(detail=True, methods=['get'])
    def accessible_modules(self, request, pk=None):
        """Get accessible modules for a staff member"""
        staff = self.get_object()
        modules = staff.get_accessible_modules()
        return Response({
            'staff_id': staff.id,
            'full_name': staff.full_name,
            'department': staff.department.name if staff.department else None,
            'accessible_modules': modules
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a staff member's account"""
        staff = self.get_object()
        staff.account_status = 'active'
        staff.save()
        return Response({'status': 'Account activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a staff member's account"""
        staff = self.get_object()
        staff.account_status = 'inactive'
        staff.save()
        return Response({'status': 'Account deactivated'})
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active staff members"""
        active_staff = self.queryset.filter(account_status='active')
        serializer = self.get_serializer(active_staff, many=True)
        return Response(serializer.data)


class SupportStaffViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SupportStaff model
    """
    queryset = SupportStaff.objects.select_related('department', 'user').all()
    serializer_class = SupportStaffSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow unauthenticated access
    filterset_fields = ['account_status', 'department', 'department__name']
    search_fields = ['full_name', 'email', 'contact']
    
    def get_serializer_class(self):
        """Use different serializer for create action"""
        if self.action == 'create':
            return SupportStaffCreateSerializer
        return SupportStaffSerializer
    
    @action(detail=True, methods=['get'])
    def accessible_modules(self, request, pk=None):
        """Get accessible modules for a support staff member"""
        support_staff = self.get_object()
        modules = support_staff.get_accessible_modules()
        return Response({
            'support_staff_id': support_staff.id,
            'full_name': support_staff.full_name,
            'department': support_staff.department.name if support_staff.department else None,
            'accessible_modules': modules
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a support staff member's account"""
        support_staff = self.get_object()
        support_staff.account_status = 'active'
        support_staff.save()
        return Response({'status': 'Account activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a support staff member's account"""
        support_staff = self.get_object()
        support_staff.account_status = 'inactive'
        support_staff.save()
        return Response({'status': 'Account deactivated'})
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active support staff members"""
        active_support_staff = self.queryset.filter(account_status='active')
        serializer = self.get_serializer(active_support_staff, many=True)
        return Response(serializer.data)