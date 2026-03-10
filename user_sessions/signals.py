from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from .models import ActiveSession
from .utils import SessionManager

@receiver(user_logged_in)
def create_user_session(sender, request, user, **kwargs):
    """Create active session when user logs in"""
    try:
        session_manager = SessionManager()
        session_manager.create_session(request, user)
        print(f"Session created for user: {user.username}")  # Debug print
    except Exception as e:
        print(f"Error creating session for {user.username}: {e}")  # Debug print

@receiver(user_logged_out)
def remove_user_session(sender, request, user, **kwargs):
    """Remove active session when user logs out"""
    try:
        if hasattr(request, 'session') and request.session.session_key:
            ActiveSession.objects.filter(
                user=user,
                session_key=request.session.session_key
            ).delete()
            print(f"Session removed for user: {user.username}")  # Debug print
    except Exception as e:
        print(f"Error removing session for {user.username}: {e}")  # Debug print

# Also handle session cleanup when Django sessions are deleted
def cleanup_orphaned_sessions():
    """Remove active sessions that no longer have corresponding Django sessions"""
    try:
        # Get all active session keys
        active_session_keys = ActiveSession.objects.values_list('session_key', flat=True)
        
        # Get all valid Django session keys
        valid_session_keys = Session.objects.values_list('session_key', flat=True)
        
        # Find orphaned sessions
        orphaned_keys = set(active_session_keys) - set(valid_session_keys)
        
        # Delete orphaned active sessions
        if orphaned_keys:
            deleted_count = ActiveSession.objects.filter(session_key__in=orphaned_keys).delete()[0]
            print(f"Cleaned up {deleted_count} orphaned sessions")
            
    except Exception as e:
        print(f"Error cleaning up orphaned sessions: {e}")
