from django.utils.deprecation import MiddlewareMixin
from .signals import set_current_request

class AuditMiddleware(MiddlewareMixin):
    """Middleware to make request available to signal handlers"""
    
    def process_request(self, request):
        set_current_request(request)
        return None
    
    def process_response(self, request, response):
        # Clear the request from thread-local storage
        set_current_request(None)
        return response
