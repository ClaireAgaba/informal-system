"""
Middleware for SchoolPay API Security
"""
from django.http import JsonResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SchoolPaySecurityMiddleware:
    """
    Middleware to secure SchoolPay API endpoints with:
    1. API Key authentication
    2. IP whitelisting
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # SchoolPay endpoints that need protection
        self.protected_paths = [
            '/api/candidates/payments/schoolpay/check-balance/',
            '/api/candidates/payments/schoolpay/callback/',
        ]
    
    def __call__(self, request):
        # Check if this is a SchoolPay endpoint
        if any(request.path.startswith(path) for path in self.protected_paths):
            # Only enforce security if SchoolPay is enabled
            if settings.SCHOOLPAY_ENABLED:
                # Validate API Key
                if not self._validate_api_key(request):
                    logger.warning(f"SchoolPay API: Invalid API key from {self._get_client_ip(request)}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Unauthorized',
                        'message': 'Invalid or missing API key'
                    }, status=401)
                
                # Validate IP Address
                if not self._validate_ip(request):
                    client_ip = self._get_client_ip(request)
                    logger.warning(f"SchoolPay API: Unauthorized IP address: {client_ip}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Forbidden',
                        'message': 'Access denied from your IP address'
                    }, status=403)
                
                # Log successful authentication
                logger.info(f"SchoolPay API: Authenticated request from {self._get_client_ip(request)}")
        
        response = self.get_response(request)
        return response
    
    def _validate_api_key(self, request):
        """
        Validate API key from request headers
        Accepts key in: X-API-Key, Authorization: Bearer <key>, or api_key query param
        """
        # Get API key from settings
        expected_key = settings.SCHOOLPAY_API_KEY
        
        # If no API key is configured, skip validation
        if not expected_key:
            return True
        
        # Check X-API-Key header
        api_key = request.headers.get('X-API-Key')
        
        # Check Authorization header (Bearer token)
        if not api_key:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header.replace('Bearer ', '')
        
        # Check query parameter (fallback)
        if not api_key:
            api_key = request.GET.get('api_key')
        
        return api_key == expected_key
    
    def _validate_ip(self, request):
        """
        Validate client IP address against whitelist
        """
        # Get allowed IPs from settings
        allowed_ips = settings.SCHOOLPAY_ALLOWED_IPS
        
        # If no IPs are configured, skip validation
        if not allowed_ips or len(allowed_ips) == 0:
            return True
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check if IP is in whitelist
        return client_ip in allowed_ips
    
    def _get_client_ip(self, request):
        """
        Get the client's IP address from the request
        Handles proxy headers (X-Forwarded-For, X-Real-IP)
        """
        # Check X-Forwarded-For header (for proxied requests)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the list
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            # Check X-Real-IP header
            ip = request.META.get('HTTP_X_REAL_IP')
            if not ip:
                # Fall back to REMOTE_ADDR
                ip = request.META.get('REMOTE_ADDR')
        
        return ip
