from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import json

class AuditLog(models.Model):
    """Main audit log model to track all user activities"""
    
    ACTION_CHOICES = [
        ('view', 'View'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('access_denied', 'Access Denied'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('search', 'Search'),
        ('filter', 'Filter'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    # Who performed the action
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=150, help_text="Stored in case user is deleted")
    
    # What action was performed
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(help_text="Human-readable description of the action")
    
    # What object was affected (generic foreign key)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    object_repr = models.CharField(max_length=200, blank=True, help_text="String representation of the object")
    
    # Additional context
    changes = models.JSONField(default=dict, blank=True, help_text="What changed (for updates)")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional context data")
    
    # Request information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    # Classification
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='low')
    module = models.CharField(max_length=50, help_text="Which module/app this relates to")
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['module', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.username} - {self.action} - {self.timestamp}"
    
    @property
    def is_sensitive(self):
        """Check if this log entry involves sensitive data"""
        sensitive_actions = ['view', 'export', 'access_denied']
        sensitive_modules = ['employees', 'users']
        return self.action in sensitive_actions or self.module in sensitive_modules

class EmployeeAccessLog(models.Model):
    """Specialized log for employee data access"""
    
    ACCESS_TYPES = [
        ('list_view', 'Employee List View'),
        ('detail_view', 'Employee Detail View'),
        ('profile_view', 'Profile View'),
        ('search', 'Employee Search'),
        ('export', 'Data Export'),
        ('edit', 'Employee Edit'),
        ('create', 'Employee Create'),
        ('delete', 'Employee Delete'),
    ]
    
    # Who accessed the data
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    username = models.CharField(max_length=150)
    
    # What employee data was accessed
    employee = models.ForeignKey('employees.Employee', on_delete=models.SET_NULL, null=True, blank=True)
    employee_id_accessed = models.CharField(max_length=20, blank=True)
    employee_name_accessed = models.CharField(max_length=200, blank=True)
    
    # Type of access
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPES)
    
    # Context
    search_query = models.CharField(max_length=500, blank=True, help_text="Search terms used")
    filters_applied = models.JSONField(default=dict, blank=True, help_text="Filters applied to the view")
    records_accessed = models.PositiveIntegerField(default=1, help_text="Number of records accessed")
    
    # Request details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField(null=True, blank=True, help_text="How long the page was viewed")
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['employee', '-timestamp']),
            models.Index(fields=['access_type', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.username} - {self.access_type} - {self.timestamp}"

class SecurityEvent(models.Model):
    """Log security-related events"""
    
    EVENT_TYPES = [
        ('failed_login', 'Failed Login Attempt'),
        ('account_locked', 'Account Locked'),
        ('permission_denied', 'Permission Denied'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('role_changed', 'Role Assignment Changed'),
        ('password_changed', 'Password Changed'),
        ('session_hijack', 'Potential Session Hijacking'),
        ('multiple_logins', 'Multiple Concurrent Logins'),
    ]
    
    RISK_LEVELS = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    # Event details
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='low')
    description = models.TextField()
    
    # User involved (may be null for anonymous attempts)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    username_attempted = models.CharField(max_length=150, blank=True)
    
    # Request details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    
    # Additional context
    metadata = models.JSONField(default=dict, blank=True)
    
    # Status
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_security_events')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['risk_level', '-timestamp']),
            models.Index(fields=['resolved', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.risk_level} - {self.timestamp}"
