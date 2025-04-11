from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication

class PointDeductionMiddleware:
    """
    Middleware to deduct points for each API request
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        # Skip point deduction for authentication endpoints and admin
        if request.path.startswith('/api/auth/') or request.path.startswith('/admin/'):
            return self.get_response(request)
        
        # Skip for non-API requests
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Authenticate user from JWT token
        try:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                validated_token = self.jwt_auth.get_validated_token(auth_header.split(' ')[1])
                user = self.jwt_auth.get_user(validated_token)
                
                # Check if user has sufficient points
                if not user.has_sufficient_points():
                    return JsonResponse(
                        {'error': 'Insufficient points to make this request.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Deduct points
                if request.path.startswith('/api/hotels/'):
                    deduction_amount = 5.0  # Deduct 5 points for hotel requests
                else:
                    deduction_amount = settings.POINT_DEDUCTION_PER_REQUEST
                
                user.deduct_points(deduction_amount)
                
                # Add user to request for views
                request.user = user
            
        except Exception as e:
            # If authentication fails, let the view handle it
            pass
        
        return self.get_response(request)
