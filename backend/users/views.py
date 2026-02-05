from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from .models import User, Staff, SupportStaff, CenterRepresentative
from .serializers import (
    UserSerializer, StaffSerializer, StaffCreateSerializer,
    SupportStaffSerializer, SupportStaffCreateSerializer,
    CenterRepresentativeSerializer, CenterRepresentativeCreateSerializer
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


@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@authentication_classes([])
def login_view(request):
    """
    Login endpoint - authenticates user and returns token
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response(
            {'error': 'Please provide both email and password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Try to find user by email
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid email or password'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Authenticate using username (since Django auth uses username)
    user_auth = authenticate(username=user.username, password=password)
    
    if user_auth is None:
        return Response(
            {'error': 'Invalid email or password'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check if user is active
    if not user.is_active:
        return Response(
            {'error': 'Account is inactive. Please contact administrator.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Get or create token
    token, created = Token.objects.get_or_create(user=user)
    
    # Get user details
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'user_type': user.user_type,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }
    
    # Add center representative specific information
    if user.user_type == 'center_representative' and hasattr(user, 'center_rep_profile'):
        center_rep = user.center_rep_profile
        user_data['center_representative'] = {
            'id': center_rep.id,
            'fullname': center_rep.fullname,
            'assessment_center': {
                'id': center_rep.assessment_center.id,
                'center_name': center_rep.assessment_center.center_name,
                'center_number': center_rep.assessment_center.center_number,
            } if center_rep.assessment_center else None,
            'assessment_center_branch': {
                'id': center_rep.assessment_center_branch.id,
                'branch_name': center_rep.assessment_center_branch.branch_name,
            } if center_rep.assessment_center_branch else None,
        }
    
    return Response({
        'token': token.key,
        'user': user_data,
        'message': 'Login successful'
    }, status=status.HTTP_200_OK)


class CenterRepresentativeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CenterRepresentative model
    """
    queryset = CenterRepresentative.objects.select_related('assessment_center', 'assessment_center_branch', 'user').all()
    serializer_class = CenterRepresentativeSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['account_status', 'assessment_center', 'assessment_center_branch']
    search_fields = ['fullname', 'email', 'contact', 'assessment_center__center_name']
    
    def get_serializer_class(self):
        """Use different serializer for create action"""
        if self.action == 'create':
            return CenterRepresentativeCreateSerializer
        return CenterRepresentativeSerializer
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Reset center representative password to default"""
        rep = self.get_object()
        if rep.user:
            rep.user.set_password('uvtab')
            rep.user.save()
            return Response({'status': 'Password reset to default (uvtab)'})
        return Response({'error': 'No user account found'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a center representative's account"""
        rep = self.get_object()
        rep.account_status = 'active'
        rep.save()
        if rep.user:
            rep.user.is_active = True
            rep.user.save()
        return Response({'status': 'Account activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a center representative's account"""
        rep = self.get_object()
        rep.account_status = 'inactive'
        rep.save()
        if rep.user:
            rep.user.is_active = False
            rep.user.save()
        return Response({'status': 'Account deactivated'})
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active center representatives"""
        active_reps = self.queryset.filter(account_status='active')
        serializer = self.get_serializer(active_reps, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def orphaned_users(self, request):
        """
        Get users with user_type='center_representative' but no CenterRepresentative profile.
        These are users created directly without a profile record.
        """
        # Find users with center_representative type who don't have a profile
        orphaned = User.objects.filter(
            user_type='center_representative'
        ).exclude(
            id__in=CenterRepresentative.objects.values_list('user_id', flat=True)
        )
        
        data = [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_active': user.is_active,
            'date_joined': user.date_joined,
            'has_profile': False,
        } for user in orphaned]
        
        return Response({
            'count': len(data),
            'results': data
        })
    
    @action(detail=False, methods=['post'])
    def link_user(self, request):
        """
        Create a CenterRepresentative profile for an existing User.
        Useful for linking orphaned users created directly in Django admin.
        """
        user_id = request.data.get('user_id')
        assessment_center_id = request.data.get('assessment_center_id')
        assessment_center_branch_id = request.data.get('assessment_center_branch_id')
        fullname = request.data.get('fullname')
        contact = request.data.get('contact')
        
        if not all([user_id, assessment_center_id, fullname, contact]):
            return Response({
                'error': 'user_id, assessment_center_id, fullname, and contact are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id, user_type='center_representative')
        except User.DoesNotExist:
            return Response({
                'error': 'User not found or not a center representative'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user already has a profile
        if CenterRepresentative.objects.filter(user=user).exists():
            return Response({
                'error': 'User already has a CenterRepresentative profile'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from assessment_centers.models import AssessmentCenter, CenterBranch
        
        try:
            center = AssessmentCenter.objects.get(id=assessment_center_id)
        except AssessmentCenter.DoesNotExist:
            return Response({
                'error': 'Assessment center not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        branch = None
        if assessment_center_branch_id:
            try:
                branch = CenterBranch.objects.get(id=assessment_center_branch_id)
            except CenterBranch.DoesNotExist:
                pass
        
        # Create the profile - email will be auto-generated in save()
        rep = CenterRepresentative(
            user=user,
            fullname=fullname,
            contact=contact,
            assessment_center=center,
            assessment_center_branch=branch,
            account_status='active' if user.is_active else 'inactive',
        )
        # Set email manually since save() won't auto-generate if user exists
        center_no = center.center_number.lower()
        if branch:
            branch_suffix = branch.branch_code.split('-')[-1].lower() if branch.branch_code else ''
            rep.email = f"{center_no}-{branch_suffix}@uvtab.go.ug"
        else:
            rep.email = f"{center_no}@uvtab.go.ug"
        
        rep.save()
        
        serializer = self.get_serializer(rep)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Logout endpoint - deletes user token
    """
    try:
        # Delete the user's token
        request.user.auth_token.delete()
        return Response(
            {'message': 'Logout successful'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )