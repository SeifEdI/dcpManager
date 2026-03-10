import re
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from .models import ActiveSession, SessionStatistics
from datetime import timedelta, date
import requests

class SessionManager:
    """Utility class for managing user sessions"""
    
    def __init__(self):
        self.cleanup_expired_sessions()
    
    def create_session(self, request, user):
        """Create or update active session for user"""
        try:
            session_key = request.session.session_key
            if not session_key:
                request.session.create()
                session_key = request.session.session_key
            
            print(f"Creating session for {user.username} with key: {session_key}")  # Debug
            
            # Get device and location info
            device_info = self.parse_user_agent(request.META.get('HTTP_USER_AGENT', ''))
            location_info = self.get_location_from_ip(self.get_client_ip(request))
            
            # Check if user has "remember me" enabled
            remember_me = request.session.get('remember_me', False)
            
            # Create or update active session
            active_session, created = ActiveSession.objects.update_or_create(
                user=user,
                session_key=session_key,
                defaults={
                    'ip_address': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'device_type': device_info['device_type'],
                    'browser': device_info['browser'],
                    'os': device_info['os'],
                    'location_city': location_info.get('city'),
                    'location_country': location_info.get('country'),
                    'last_activity': timezone.now(),
                    'is_active': True,
                    'remember_me': remember_me,
                }
            )
            
            print(f"Session {'created' if created else 'updated'} for {user.username}")  # Debug
            
            # Update session statistics
            self.update_daily_statistics()
            
            return active_session
            
        except Exception as e:
            print(f"Error in create_session: {e}")
            return None
    
    def update_session_activity(self, request):
        """Update last activity for current session"""
        try:
            if request.user.is_authenticated and hasattr(request, 'session'):
                session_key = request.session.session_key
                if session_key:
                    updated = ActiveSession.objects.filter(
                        user=request.user,
                        session_key=session_key
                    ).update(last_activity=timezone.now())
                    
                    if updated == 0:
                        # Session doesn't exist, create it
                        self.create_session(request, request.user)
        except Exception as e:
            print(f"Error updating session activity: {e}")
    
    def get_active_sessions(self):
        """Get all active sessions"""
        try:
            self.cleanup_expired_sessions()
            sessions = ActiveSession.objects.filter(is_active=True).select_related('user')
            print(f"Found {sessions.count()} active sessions")  # Debug
            return sessions
        except Exception as e:
            print(f"Error getting active sessions: {e}")
            return ActiveSession.objects.none()
    
    def get_user_sessions(self, user):
        """Get active sessions for specific user"""
        try:
            return ActiveSession.objects.filter(user=user, is_active=True)
        except Exception as e:
            print(f"Error getting user sessions: {e}")
            return ActiveSession.objects.none()
    
    def force_logout_user(self, user, session_key=None):
        """Force logout user (all sessions or specific session)"""
        try:
            if session_key:
                # Logout specific session
                sessions = ActiveSession.objects.filter(user=user, session_key=session_key)
            else:
                # Logout all user sessions
                sessions = ActiveSession.objects.filter(user=user, is_active=True)
            
            # Delete Django sessions
            for active_session in sessions:
                try:
                    django_session = Session.objects.get(session_key=active_session.session_key)
                    django_session.delete()
                except Session.DoesNotExist:
                    pass
            
            # Delete active session records
            deleted_count = sessions.delete()[0]
            print(f"Force logged out {deleted_count} sessions for {user.username}")
            
        except Exception as e:
            print(f"Error force logging out user: {e}")
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        try:
            now = timezone.now()
            
            # Find expired sessions
            expired_sessions = []
            for session in ActiveSession.objects.filter(is_active=True):
                if session.is_expired:
                    expired_sessions.append(session.session_key)
            
            if expired_sessions:
                # Delete expired Django sessions
                Session.objects.filter(session_key__in=expired_sessions).delete()
                
                # Delete expired active sessions
                deleted_count = ActiveSession.objects.filter(session_key__in=expired_sessions).delete()[0]
                print(f"Cleaned up {deleted_count} expired sessions")
                
        except Exception as e:
            print(f"Error cleaning up expired sessions: {e}")
    
    def get_session_statistics(self):
        """Get current session statistics"""
        try:
            active_sessions = self.get_active_sessions()
            
            total_connected = active_sessions.count()
            active_count = sum(1 for s in active_sessions if s.status == 'active')
            mobile_count = active_sessions.filter(device_type='mobile').count()
            desktop_count = active_sessions.filter(device_type='desktop').count()
            
            stats = {
                'total_connected': total_connected,
                'active_sessions': active_count,
                'idle_sessions': total_connected - active_count,
                'mobile_sessions': mobile_count,
                'desktop_sessions': desktop_count,
                'unique_users': active_sessions.values('user').distinct().count(),
            }
            
            print(f"Session statistics: {stats}")  # Debug
            return stats
            
        except Exception as e:
            print(f"Error getting session statistics: {e}")
            return {
                'total_connected': 0,
                'active_sessions': 0,
                'idle_sessions': 0,
                'mobile_sessions': 0,
                'desktop_sessions': 0,
                'unique_users': 0,
            }
    
    def update_daily_statistics(self):
        """Update daily session statistics"""
        try:
            today = date.today()
            current_stats = self.get_session_statistics()
            
            stats, created = SessionStatistics.objects.get_or_create(
                date=today,
                defaults={
                    'total_sessions': 0,
                    'unique_users': 0,
                    'peak_concurrent': 0,
                    'mobile_sessions': 0,
                    'desktop_sessions': 0,
                }
            )
            
            # Update peak concurrent if current is higher
            if current_stats['total_connected'] > stats.peak_concurrent:
                stats.peak_concurrent = current_stats['total_connected']
            
            stats.unique_users = current_stats['unique_users']
            stats.mobile_sessions = current_stats['mobile_sessions']
            stats.desktop_sessions = current_stats['desktop_sessions']
            stats.save()
            
        except Exception as e:
            print(f"Error updating daily statistics: {e}")
    
    def parse_user_agent(self, user_agent):
        """Parse user agent string to extract device info"""
        if not user_agent:
            return {'device_type': 'unknown', 'browser': 'unknown', 'os': 'unknown'}
        
        # Device type detection
        device_type = 'desktop'
        if re.search(r'Mobile|Android|iPhone|iPad', user_agent, re.I):
            device_type = 'mobile'
        elif re.search(r'Tablet|iPad', user_agent, re.I):
            device_type = 'tablet'
        
        # Browser detection
        browser = 'unknown'
        if 'Chrome' in user_agent:
            browser = 'Chrome'
        elif 'Firefox' in user_agent:
            browser = 'Firefox'
        elif 'Safari' in user_agent and 'Chrome' not in user_agent:
            browser = 'Safari'
        elif 'Edge' in user_agent:
            browser = 'Edge'
        elif 'Opera' in user_agent:
            browser = 'Opera'
        
        # OS detection
        os = 'unknown'
        if 'Windows' in user_agent:
            os = 'Windows'
        elif 'Mac OS' in user_agent:
            os = 'macOS'
        elif 'Linux' in user_agent:
            os = 'Linux'
        elif 'Android' in user_agent:
            os = 'Android'
        elif 'iOS' in user_agent or 'iPhone' in user_agent or 'iPad' in user_agent:
            os = 'iOS'
        
        return {
            'device_type': device_type,
            'browser': browser,
            'os': os
        }
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or '127.0.0.1'
    
    def get_location_from_ip(self, ip_address):
        """Get approximate location from IP address"""
        if ip_address in ['127.0.0.1', 'localhost']:
            return {'city': 'Local', 'country': 'Local'}
        
        try:
            # Using a free IP geolocation service
            response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    return {
                        'city': data.get('city', 'Unknown'),
                        'country': data.get('country', 'Unknown')
                    }
        except:
            pass
        
        return {'city': 'Unknown', 'country': 'Unknown'}
