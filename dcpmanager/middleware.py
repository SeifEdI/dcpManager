from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
import time

class SessionSecurityMiddleware(MiddlewareMixin):
    """Middleware to handle session security and timeout"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Check if this is a "remember me" session
            session_expiry = request.session.get_expiry_age()
            is_remember_me_session = session_expiry > 7200  # More than 2 hours indicates remember me
            
            # Different timeout rules for different session types
            if not is_remember_me_session:
                # Regular session - 30 minutes of inactivity
                last_activity = request.session.get('last_activity')
                if last_activity:
                    time_since_last_activity = time.time() - last_activity
                    if time_since_last_activity > 1800:  # 30 minutes
                        logout(request)
                        messages.warning(request, 'Your session has expired due to inactivity. Please login again.')
                        return redirect('login')
                
                # Update last activity time for regular sessions
                request.session['last_activity'] = time.time()
            else:
                # Remember me session - just update last activity without timeout check
                request.session['last_activity'] = time.time()
        
        return None
