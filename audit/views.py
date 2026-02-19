from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from rbac.decorators import rbac_required
from .models import AuditLog, EmployeeAccessLog, SecurityEvent
from .utils import AuditLogger

@login_required
@rbac_required('system.logs', redirect_url='dashboard')
def audit_dashboard(request):
    """Main audit dashboard showing overview of system activity"""
    
    # Get date range (default to last 30 days)
    days = int(request.GET.get('days', 30))
    since = timezone.now() - timedelta(days=days)
    
    # General statistics
    total_actions = AuditLog.objects.filter(timestamp__gte=since).count()
    total_employee_access = EmployeeAccessLog.objects.filter(timestamp__gte=since).count()
    total_security_events = SecurityEvent.objects.filter(timestamp__gte=since).count()
    unresolved_security_events = SecurityEvent.objects.filter(
        timestamp__gte=since, 
        resolved=False
    ).count()
    
    # Top users by activity
    top_users = AuditLog.objects.filter(
        timestamp__gte=since
    ).values('username').annotate(
        action_count=Count('id')
    ).order_by('-action_count')[:10]
    
    # Actions by type
    actions_by_type = AuditLog.objects.filter(
        timestamp__gte=since
    ).values('action').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Employee access by type
    employee_access_by_type = EmployeeAccessLog.objects.filter(
        timestamp__gte=since
    ).values('access_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Security events by type
    security_events_by_type = SecurityEvent.objects.filter(
        timestamp__gte=since
    ).values('event_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent high-severity events
    recent_high_severity = AuditLog.objects.filter(
        timestamp__gte=since,
        severity__in=['high', 'critical']
    ).order_by('-timestamp')[:10]
    
    context = {
        'title': 'Audit Dashboard',
        'days': days,
        'total_actions': total_actions,
        'total_employee_access': total_employee_access,
        'total_security_events': total_security_events,
        'unresolved_security_events': unresolved_security_events,
        'top_users': top_users,
        'actions_by_type': actions_by_type,
        'employee_access_by_type': employee_access_by_type,
        'security_events_by_type': security_events_by_type,
        'recent_high_severity': recent_high_severity,
    }
    return render(request, 'audit/dashboard.html', context)

@login_required
@rbac_required('system.logs', redirect_url='dashboard')
def audit_logs(request):
    """View audit logs with filtering"""
    
    logs = AuditLog.objects.all()
    
    # Apply filters
    action = request.GET.get('action')
    if action:
        logs = logs.filter(action=action)
    
    module = request.GET.get('module')
    if module:
        logs = logs.filter(module=module)
    
    severity = request.GET.get('severity')
    if severity:
        logs = logs.filter(severity=severity)
    
    username = request.GET.get('username')
    if username:
        logs = logs.filter(username__icontains=username)
    
    date_from = request.GET.get('date_from')
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    actions = AuditLog.objects.values_list('action', flat=True).distinct()
    modules = AuditLog.objects.values_list('module', flat=True).distinct()
    severities = AuditLog.objects.values_list('severity', flat=True).distinct()
    
    context = {
        'title': 'Audit Logs',
        'page_obj': page_obj,
        'actions': actions,
        'modules': modules,
        'severities': severities,
        'current_filters': {
            'action': action,
            'module': module,
            'severity': severity,
            'username': username,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'audit/logs.html', context)

@login_required
@rbac_required('system.logs', redirect_url='dashboard')
def employee_access_logs(request):
    """View employee access logs"""
    
    logs = EmployeeAccessLog.objects.select_related('user', 'employee').all()
    
    # Apply filters
    access_type = request.GET.get('access_type')
    if access_type:
        logs = logs.filter(access_type=access_type)
    
    username = request.GET.get('username')
    if username:
        logs = logs.filter(username__icontains=username)
    
    employee_search = request.GET.get('employee')
    if employee_search:
        logs = logs.filter(
            Q(employee_name_accessed__icontains=employee_search) |
            Q(employee_id_accessed__icontains=employee_search)
        )
    
    date_from = request.GET.get('date_from')
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    access_types = EmployeeAccessLog.objects.values_list('access_type', flat=True).distinct()
    
    context = {
        'title': 'Employee Access Logs',
        'page_obj': page_obj,
        'access_types': access_types,
        'current_filters': {
            'access_type': access_type,
            'username': username,
            'employee': employee_search,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'audit/employee_access_logs.html', context)

@login_required
@rbac_required('system.logs', redirect_url='dashboard')
def security_events(request):
    """View security events"""
    
    events = SecurityEvent.objects.all()
    
    # Apply filters
    event_type = request.GET.get('event_type')
    if event_type:
        events = events.filter(event_type=event_type)
    
    risk_level = request.GET.get('risk_level')
    if risk_level:
        events = events.filter(risk_level=risk_level)
    
    resolved = request.GET.get('resolved')
    if resolved == 'true':
        events = events.filter(resolved=True)
    elif resolved == 'false':
        events = events.filter(resolved=False)
    
    username = request.GET.get('username')
    if username:
        events = events.filter(username_attempted__icontains=username)
    
    # Pagination
    paginator = Paginator(events, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    event_types = SecurityEvent.objects.values_list('event_type', flat=True).distinct()
    risk_levels = SecurityEvent.objects.values_list('risk_level', flat=True).distinct()
    
    context = {
        'title': 'Security Events',
        'page_obj': page_obj,
        'event_types': event_types,
        'risk_levels': risk_levels,
        'current_filters': {
            'event_type': event_type,
            'risk_level': risk_level,
            'resolved': resolved,
            'username': username,
        }
    }
    return render(request, 'audit/security_events.html', context)

@login_required
def my_activity(request):
    """View current user's activity logs"""
    
    # Get user's audit logs
    audit_logs = AuditLog.objects.filter(user=request.user).order_by('-timestamp')[:50]
    
    # Get user's employee access logs
    employee_logs = EmployeeAccessLog.objects.filter(user=request.user).order_by('-timestamp')[:50]
    
    # Get activity summary
    activity_summary = AuditLogger.get_user_activity_summary(request.user, days=30)
    
    context = {
        'title': 'My Activity',
        'audit_logs': audit_logs,
        'employee_logs': employee_logs,
        'activity_summary': activity_summary,
    }
    return render(request, 'audit/my_activity.html', context)
