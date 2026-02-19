from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .utils import SessionManager

@login_required
@require_http_methods(["GET"])
def session_status(request):
    """API endpoint to check session status"""
    session_info = SessionManager.get_session_info(request)
    
    if not session_info:
        return JsonResponse({
            'authenticated': False,
            'message': 'Not authenticated'
        })
    
    return JsonResponse({
        'authenticated': True,
        'session_type': session_info['session_type'],
        'remember_me': session_info['remember_me'],
        'time_remaining': session_info['time_remaining'],
        'username': request.user.username,
        'full_name': request.user.get_full_name() or request.user.username
    })

def session_expired(request):
    """View for handling expired sessions"""
    return JsonResponse({
        'authenticated': False,
        'message': 'Session expired'
    })
