# middleware.py
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
import logging
from django.shortcuts import render

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
    


class AuthErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if getattr(exception, 'status_code', None) == 401:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Требуется авторизация',
                    'login_url': reverse('login')
                }, status=401)
            return HttpResponseRedirect(f"{reverse('login')}?next={request.path}")
        
        if getattr(exception, 'status_code', None) == 403:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Доступ запрещен',
                    'detail': str(exception)
                }, status=403)
            return render(request, 'errors/403.html', status=403)