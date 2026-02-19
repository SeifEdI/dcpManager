from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import AuditLog, EmployeeAccessLog, SecurityEvent

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'username', 'action', 'module', 'object_repr', 'severity', 'ip_address']
    list_filter = ['action', 'module', 'severity', 'timestamp', 'content_type']
    search_fields = ['username', 'description', 'object_repr', 'ip_address']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'username', 'ip_address', 'user_agent')
        }),
        ('Action Details', {
            'fields': ('action', 'description', 'module', 'severity')
        }),
        ('Object Information', {
            'fields': ('content_type', 'object_id', 'object_repr')
        }),
        ('Request Details', {
            'fields': ('request_path', 'request_method')
        }),
        ('Additional Data', {
            'fields': ('changes', 'metadata'),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(EmployeeAccessLog)
class EmployeeAccessLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'username', 'access_type', 'employee_name_accessed', 'records_accessed', 'ip_address']
    list_filter = ['access_type', 'timestamp']
    search_fields = ['username', 'employee_name_accessed', 'employee_id_accessed', 'search_query']
    readonly_fields = ['timestamp', 'duration']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Access Information', {
            'fields': ('user', 'username', 'access_type', 'timestamp')
        }),
        ('Employee Data', {
            'fields': ('employee', 'employee_id_accessed', 'employee_name_accessed', 'records_accessed')
        }),
        ('Context', {
            'fields': ('search_query', 'filters_applied', 'duration')
        }),
        ('Request Details', {
            'fields': ('ip_address', 'user_agent', 'session_key')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'event_type', 'risk_level', 'username_attempted', 'resolved_status', 'ip_address']
    list_filter = ['event_type', 'risk_level', 'resolved', 'timestamp']
    search_fields = ['username_attempted', 'description', 'ip_address']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'risk_level', 'description', 'timestamp')
        }),
        ('User Information', {
            'fields': ('user', 'username_attempted')
        }),
        ('Request Details', {
            'fields': ('ip_address', 'user_agent', 'request_path')
        }),
        ('Resolution', {
            'fields': ('resolved', 'resolved_by', 'resolved_at', 'resolution_notes')
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def resolved_status(self, obj):
        if obj.resolved:
            return format_html('<span style="color: green;">✓ Resolved</span>')
        else:
            return format_html('<span style="color: red;">✗ Unresolved</span>')
    resolved_status.short_description = 'Status'
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
