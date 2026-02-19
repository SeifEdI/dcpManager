from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.contrib.auth.models import User
from employees.models import Employee
from rbac.models import UserRole
from .utils import AuditLogger
from .models import SecurityEvent
import threading

# Thread-local storage for request information
_thread_locals = threading.local()

def set_current_request(request):
    """Store the current request in thread-local storage"""
    _thread_locals.request = request

def get_current_request():
    """Get the current request from thread-local storage"""
    return getattr(_thread_locals, 'request', None)

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Log successful user logins"""
    AuditLogger.log_action(
        user=user,
        action='login',
        description=f'User {user.username} logged in successfully',
        request=request,
        severity='low',
        module='authentication'
    )
    
    AuditLogger.log_security_event(
        event_type='login',
        description=f'Successful login for user {user.username}',
        risk_level='low',
        user=user,
        request=request
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Log user logouts"""
    if user:  # user might be None if session expired
        AuditLogger.log_action(
            user=user,
            action='logout',
            description=f'User {user.username} logged out',
            request=request,
            severity='low',
            module='authentication'
        )

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """Log failed login attempts"""
    username = credentials.get('username', 'Unknown')
    
    AuditLogger.log_security_event(
        event_type='failed_login',
        description=f'Failed login attempt for username: {username}',
        risk_level='medium',
        username_attempted=username,
        request=request
    )
    
    # Check for suspicious activity (multiple failed attempts)
    from django.utils import timezone
    from datetime import timedelta
    
    recent_failures = SecurityEvent.objects.filter(
        event_type='failed_login',
        username_attempted=username,
        timestamp__gte=timezone.now() - timedelta(minutes=15)
    ).count()
    
    if recent_failures >= 5:
        AuditLogger.log_security_event(
            event_type='suspicious_activity',
            description=f'Multiple failed login attempts for username: {username} ({recent_failures} attempts in 15 minutes)',
            risk_level='high',
            username_attempted=username,
            request=request,
            metadata={'failed_attempts': recent_failures}
        )

@receiver(post_save, sender=Employee)
def log_employee_changes(sender, instance, created, **kwargs):
    """Log employee creation and updates"""
    request = get_current_request()
    user = getattr(request, 'user', None) if request else None
    
    if created:
        AuditLogger.log_action(
            user=user,
            action='create',
            description=f'Created new employee: {instance.full_name} (ID: {instance.employee_id})',
            obj=instance,
            request=request,
            severity='medium',
            module='employees'
        )
    else:
        # For updates, we'd need to track what changed
        # This is a simplified version - you could enhance it to track specific field changes
        AuditLogger.log_action(
            user=user,
            action='update',
            description=f'Updated employee: {instance.full_name} (ID: {instance.employee_id})',
            obj=instance,
            request=request,
            severity='medium',
            module='employees'
        )

@receiver(post_delete, sender=Employee)
def log_employee_deletion(sender, instance, **kwargs):
    """Log employee deletions"""
    request = get_current_request()
    user = getattr(request, 'user', None) if request else None
    
    AuditLogger.log_action(
        user=user,
        action='delete',
        description=f'Deleted employee: {instance.full_name} (ID: {instance.employee_id})',
        obj=instance,
        request=request,
        severity='high',
        module='employees'
    )

@receiver(post_save, sender=UserRole)
def log_role_assignment(sender, instance, created, **kwargs):
    """Log role assignments and changes"""
    request = get_current_request()
    user = getattr(request, 'user', None) if request else None
    
    if created:
        AuditLogger.log_action(
            user=user,
            action='create',
            description=f'Assigned role "{instance.role.name}" to user {instance.user.username}',
            obj=instance,
            request=request,
            severity='high',
            module='rbac'
        )
        
        AuditLogger.log_security_event(
            event_type='role_changed',
            description=f'Role "{instance.role.name}" assigned to user {instance.user.username}',
            risk_level='medium',
            user=instance.user,
            request=request,
            metadata={
                'role_assigned': instance.role.name,
                'assigned_by': user.username if user else 'System'
            }
        )

@receiver(post_delete, sender=UserRole)
def log_role_removal(sender, instance, **kwargs):
    """Log role removals"""
    request = get_current_request()
    user = getattr(request, 'user', None) if request else None
    
    AuditLogger.log_action(
        user=user,
        action='delete',
        description=f'Removed role "{instance.role.name}" from user {instance.user.username}',
        obj=instance,
        request=request,
        severity='high',
        module='rbac'
    )
    
    AuditLogger.log_security_event(
        event_type='role_changed',
        description=f'Role "{instance.role.name}" removed from user {instance.user.username}',
        risk_level='medium',
        user=instance.user,
        request=request,
        metadata={
            'role_removed': instance.role.name,
            'removed_by': user.username if user else 'System'
        }
    )
