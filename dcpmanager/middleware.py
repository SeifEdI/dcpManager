from django.utils import timezone
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from datetime import datetime
import time

class SessionSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Update session activity if user is authenticated
        if request.user.is_authenticated:
            try:
                from user_sessions.utils import SessionManager
                session_manager = SessionManager()
                session_manager.update_session_activity(request)
            except ImportError:
                # If user_sessions app is not available, skip session tracking
                pass
            
            # Check for session timeout
            if self.is_session_expired(request):
                logout(request)
                messages.warning(request, 'Your session has expired. Please log in again.')
                return redirect(reverse('login'))

        response = self.get_response(request)
        return response

    def is_session_expired(self, request):
        """Check if the current session has expired"""
        if not hasattr(request, 'session') or not request.session.session_key:
            return False
            
        try:
            # Get session timeout setting
            remember_me = request.session.get('remember_me', False)
            if remember_me:
                timeout = 30 * 24 * 60 * 60  # 30 days in seconds
            else:
                timeout = 30 * 60  # 30 minutes in seconds
                
            # Check last activity using timestamp approach
            last_activity = request.session.get('last_activity')
            current_time = time.time()
            
            if last_activity:
                # Handle different formats of last_activity
                if isinstance(last_activity, str):
                    try:
                        # Try to parse ISO format
                        last_activity_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                        last_activity_timestamp = last_activity_dt.timestamp()
                    except (ValueError, AttributeError):
                        # If parsing fails, treat as expired
                        return True
                elif isinstance(last_activity, (int, float)):
                    # Already a timestamp
                    last_activity_timestamp = last_activity
                else:
                    # Unknown format, treat as expired
                    return True
                
                # Check if session has expired
                if (current_time - last_activity_timestamp) > timeout:
                    return True
                    
            # Update last activity with current timestamp
            request.session['last_activity'] = current_time
            return False
            
        except Exception as e:
            # If any error occurs, don't expire the session to avoid breaking the app
            # Just update the last activity and continue
            request.session['last_activity'] = time.time()
            return False
