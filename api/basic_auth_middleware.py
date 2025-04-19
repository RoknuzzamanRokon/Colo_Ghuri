import base64
from django.contrib.auth import authenticate, get_user_model
from django.http import HttpResponse
from django.conf import settings

class BasicAuthenticationMiddleware:
    """
    Middleware to authenticate requests using HTTP Basic Authentication.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        if auth_header and auth_header.startswith('Basic '):
            try:
                auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
                username, password = auth_decoded.split(':', 1)
                user = authenticate(request, username=username, password=password)

                user = authenticate(request, username=username, password=password)

                if user is not None and user.is_superuser:
                    request.user = user
                else:
                    request.user = None  # Set user to None if authentication fails
                    return self.get_response(request)
            except Exception:
                request.user = None # Set user to None if authentication fails
                return self.get_response(request)

        return self.get_response(request)
