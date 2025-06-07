# middleware.py
import logging
from django.shortcuts import redirect

logger = logging.getLogger(__name__)

class LogUnauthorizedAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if response.status_code == 302 and 'login' in response.url:
            logger.warning(f"Unauthorized access attempt to {request.path} by {request.META.get('REMOTE_ADDR')}")
        
        return response


class LogJWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Логируем заголовок Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            print(f"JWT Header: {auth_header[:50]}...")
        
        response = self.get_response(request)
        return response