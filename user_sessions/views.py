from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from rbac.decorators import rbac_required
from .models import ActiveSession, SessionStatistics
from .utils import SessionManager
from datetime import timedelta

@login_required
@rbac_required('user_sessions.view_activesession', redirect_url='dashboard')
def connected_users(request):
    """View connected users with filtering and pagination"""
    session_manager = SessionManager()
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    device_filter = request.GET.get('device', '')
    status_filter = request.GET.get('status', '')
    
    # Get active sessions
    sessions = session_manager.get_active_sessions()
    
    # Apply filters
    if search_query:
        sessions = sessions.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(ip_address__icontains=search_query)
        )
    
    if device_filter:
        sessions = sessions.filter(device_type=device_filter)
    
    if status_filter:
        # Filter by status (this requires checking each session)
        filtered_sessions = []
        for session in sessions:
            if session.status == status_filter:
                filtered_sessions.append(session.id)
        sessions = sessions.filter(id__in=filtered_sessions)
    
    # Pagination
    paginator = Paginator(sessions, 20)  # 20 sessions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    stats = session_manager.get_session_statistics()
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'search_query': search_query,
        'device_filter': device_filter,
        'status_filter': status_filter,
        'device_choices': ['mobile', 'desktop', 'tablet'],
        'status_choices': ['active', 'idle', 'away'],
    }
    
    return render(request, 'user_sessions/connected_users.html', context)

@login_required
def debug_sessions(request):
    """Debug view to check session tracking"""
    from django.contrib.sessions.models import Session
    
    # Get all active sessions from our model
    active_sessions = ActiveSession.objects.all()
    
    # Get all Django sessions
    django_sessions = Session.objects.all()
    
    # Current user's session
    current_session_key = request.session.session_key
    
    debug_info = {
        'active_sessions_count': active_sessions.count(),
        'django_sessions_count': django_sessions.count(),
        'current_session_key': current_session_key,
        'active_sessions': list(active_sessions.values()),
        'django_sessions': list(django_sessions.values()),
    }
    
    return JsonResponse(debug_info, indent=2)

@login_required
@rbac_required('user_sessions.view_activesession', redirect_url='dashboard')
def session_detail(request, session_id):
    """View detailed information about a specific session"""
    session = get_object_or_404(ActiveSession, id=session_id)
    
    context = {
        'session': session,
    }
    
    return render(request, 'user_sessions/session_detail.html', context)

@login_required
@rbac_required('user_sessions.delete_activesession', redirect_url='dashboard')
def force_logout(request, session_id):
    """Force logout a specific session"""
    session = get_object_or_404(ActiveSession, id=session_id)
    session_manager = SessionManager()
    
    if request.method == 'POST':
        username = session.user.username
        session_manager.force_logout_user(session.user, session.session_key)
        messages.success(request, f'Successfully logged out {username}')
        return redirect('user_sessions:connected_users')
    
    context = {
        'session': session,
    }
    
    return render(request, 'user_sessions/confirm_logout.html', context)

@login_required
def my_sessions(request):
    """View current user's active sessions"""
    session_manager = SessionManager()
    sessions = session_manager.get_user_sessions(request.user)
    
    context = {
        'sessions': sessions,
        'current_session_key': request.session.session_key,
    }
    
    return render(request, 'user_sessions/my_sessions.html', context)

@login_required
@rbac_required('user_sessions.view_activesession', redirect_url='dashboard')
def api_connected_users(request):
    """API endpoint for connected users data"""
    session_manager = SessionManager()
    sessions = session_manager.get_active_sessions()
    
    data = []
    for session in sessions:
        data.append({
            'id': session.id,
            'username': session.user.username,
            'full_name': session.user.get_full_name() or session.user.username,
            'device_type': session.device_type,
            'browser': session.browser,
            'os': session.os,
            'ip_address': session.ip_address,
            'location': f"{session.location_city}, {session.location_country}" if session.location_city else "Unknown",
            'status': session.status,
            'duration': str(session.duration).split('.')[0],  # Remove microseconds
            'last_activity': session.last_activity.strftime('%Y-%m-%d %H:%M:%S'),
            'created_at': session.created_at.strftime('%Y-%m-%d %H:%M:%S'),  
        })
    
    return JsonResponse({
        'sessions': data,
        'count': len(data)
    })

@login_required
@rbac_required('user_sessions.view_activesession', redirect_url='dashboard')
def api_statistics(request):
    """API endpoint for session statistics"""
    session_manager = SessionManager()
    stats = session_manager.get_session_statistics()
    
    return JsonResponse(stats)
