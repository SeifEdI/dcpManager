from django.conf import settings
import time

class SessionManager:
    """Utility class for managing different types of sessions"""
    
    @staticmethod
    def set_remember_me_session(request):
        """Set session for remember me functionality"""
        request.session.set_expiry(getattr(settings, 'REMEMBER_ME_DURATION', 30 * 24 * 60 * 60))
        request.session['remember_me'] = True
        request.session['session_type'] = 'remember_me'
        request.session['last_activity'] = time.time()
    
    @staticmethod
    def set_regular_session(request):
        """Set regular session that expires when browser closes"""
        request.session.set_expiry(0)  # Expire when browser closes
        request.session['remember_me'] = False
        request.session['session_type'] = 'regular'
        request.session['last_activity'] = time.time()
    
    @staticmethod
    def is_remember_me_session(request):
        """Check if current session is a remember me session"""
        return request.session.get('remember_me', False)
    
    @staticmethod
    def get_session_info(request):
        """Get information about the current session"""
        if not request.user.is_authenticated:
            return None
        
        session_type = request.session.get('session_type', 'unknown')
        last_activity = request.session.get('last_activity', time.time())
        remember_me = request.session.get('remember_me', False)
        
        if remember_me:
            # For remember me sessions, calculate time until absolute expiry
            session_expiry = request.session.get_expiry_date()
            if session_expiry:
                time_remaining = (session_expiry.timestamp() - time.time())
            else:
                time_remaining = getattr(settings, 'REMEMBER_ME_DURATION', 30 * 24 * 60 * 60)
        else:
            # For regular sessions, calculate time until inactivity timeout
            time_since_activity = time.time() - last_activity
            time_remaining = getattr(settings, 'REGULAR_SESSION_TIMEOUT', 30 * 60) - time_since_activity
        
        return {
            'session_type': session_type,
            'remember_me': remember_me,
            'time_remaining': max(0, int(time_remaining)),
            'last_activity': last_activity
        }
