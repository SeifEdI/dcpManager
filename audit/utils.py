from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import AuditLog, EmployeeAccessLog, SecurityEvent
import json

class AuditLogger:
    """Utility class for creating audit log entries"""
    
    @staticmethod
    def log_action(user, action, description, obj=None, changes=None, metadata=None, 
                   request=None, severity='low', module='general'):
        """
        Create a general audit log entry
        
        Args:
            user: User who performed the action
            action: Type of action (from ACTION_CHOICES)
            description: Human-readable description
            obj: Object that was affected (optional)
            changes: Dict of what changed (for updates)
            metadata: Additional context data
            request: HTTP request object (for IP, user agent, etc.)
            severity: Severity level
            module: Which module this relates to
        """
        log_data = {
            'user': user,
            'username': user.username if user else 'Anonymous',
            'action': action,
            'description': description,
            'severity': severity,
            'module': module,
            'changes': changes or {},
            'metadata': metadata or {},
        }
        
        # Add object information if provided
        if obj:
            log_data.update({
                'content_type': ContentType.objects.get_for_model(obj),
                'object_id': obj.pk,
                'object_repr': str(obj)[:200],
            })
        
        # Add request information if provided
        if request:
            log_data.update({
                'ip_address': AuditLogger.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'request_path': request.path,
                'request_method': request.method,
            })
        
        return AuditLog.objects.create(**log_data)
    
    @staticmethod
    def log_employee_access(user, access_type, employee=None, search_query='', 
                           filters=None, records_count=1, request=None):
        """
        Log employee data access
        
        Args:
            user: User accessing the data
            access_type: Type of access (from ACCESS_TYPES)
            employee: Specific employee accessed (optional)
            search_query: Search terms used
            filters: Filters applied
            records_count: Number of records accessed
            request: HTTP request object
        """
        log_data = {
            'user': user,
            'username': user.username if user else 'Anonymous',
            'access_type': access_type,
            'search_query': search_query,
            'filters_applied': filters or {},
            'records_accessed': records_count,
        }
        
        # Add employee information if provided
        if employee:
            log_data.update({
                'employee': employee,
                'employee_id_accessed': employee.employee_id,
                'employee_name_accessed': employee.full_name,
            })
        
        # Add request information if provided
        if request:
            log_data.update({
                'ip_address': AuditLogger.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'session_key': request.session.session_key,
            })
        
        return EmployeeAccessLog.objects.create(**log_data)
    
    @staticmethod
    def log_security_event(event_type, description, risk_level='low', user=None, 
                          username_attempted='', request=None, metadata=None):
        """
        Log security-related events
        
        Args:
            event_type: Type of security event
            description: Description of what happened
            risk_level: Risk level of the event
            user: User involved (if any)
            username_attempted: Username that was attempted (for failed logins)
            request: HTTP request object
            metadata: Additional context data
        """
        log_data = {
            'event_type': event_type,
            'risk_level': risk_level,
            'description': description,
            'user': user,
            'username_attempted': username_attempted,
            'metadata': metadata or {},
        }
        
        # Add request information if provided
        if request:
            log_data.update({
                'ip_address': AuditLogger.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
                'request_path': request.path,
            })
        
        return SecurityEvent.objects.create(**log_data)
    
    @staticmethod
    def get_client_ip(request):
        """Get the client's IP address from the request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def get_user_activity_summary(user, days=30):
        """Get a summary of user's recent activity"""
        from django.utils import timezone
        from datetime import timedelta
        
        since = timezone.now() - timedelta(days=days)
        
        # General audit logs
        audit_logs = AuditLog.objects.filter(
            user=user,
            timestamp__gte=since
        ).values('action').annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        # Employee access logs
        employee_access = EmployeeAccessLog.objects.filter(
            user=user,
            timestamp__gte=since
        ).values('access_type').annotate(
            count=models.Count('id')
        ).order_by('-count')
        
        # Security events
        security_events = SecurityEvent.objects.filter(
            user=user,
            timestamp__gte=since
        ).count()
        
        return {
            'audit_logs': list(audit_logs),
            'employee_access': list(employee_access),
            'security_events': security_events,
            'total_actions': sum(log['count'] for log in audit_logs),
            'period_days': days,
        }

class AuditDecorator:
    """Decorator class for automatically logging function calls"""
    
    @staticmethod
    def log_employee_access(access_type, get_employee=None):
        """
        Decorator to automatically log employee data access
        
        Args:
            access_type: Type of access being logged
            get_employee: Function to extract employee from view args/kwargs
        """
        def decorator(view_func):
            def wrapper(request, *args, **kwargs):
                # Execute the view
                response = view_func(request, *args, **kwargs)
                
                # Log the access
                employee = None
                if get_employee:
                    try:
                        employee = get_employee(*args, **kwargs)
                    except:
                        pass
                
                # Extract search and filter info from request
                search_query = request.GET.get('search', '')
                filters = {k: v for k, v in request.GET.items() 
                          if k in ['type', 'status', 'department'] and v}
                
                # Count records if it's a list view
                records_count = 1
                if hasattr(response, 'context_data') and 'page_obj' in response.context_data:
                    page_obj = response.context_data['page_obj']
                    records_count = len(page_obj.object_list) if page_obj else 0
                
                AuditLogger.log_employee_access(
                    user=request.user,
                    access_type=access_type,
                    employee=employee,
                    search_query=search_query,
                    filters=filters,
                    records_count=records_count,
                    request=request
                )
                
                return response
            return wrapper
        return decorator
