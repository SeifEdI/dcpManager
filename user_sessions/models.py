from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class ActiveSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='active_sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=20, default='unknown')
    browser = models.CharField(max_length=50, default='unknown')
    os = models.CharField(max_length=50, default='unknown')
    location_city = models.CharField(max_length=100, blank=True, null=True)
    location_country = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    remember_me = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type} ({self.ip_address})"
    
    @property
    def duration(self):
        """Get session duration"""
        return timezone.now() - self.created_at
    
    @property
    def status(self):
        """Get session status based on last activity"""
        now = timezone.now()
        if self.last_activity > now - timedelta(minutes=5):
            return 'active'
        elif self.last_activity > now - timedelta(minutes=30):
            return 'idle'
        else:
            return 'away'
    
    @property
    def is_expired(self):
        """Check if session is expired"""
        if self.remember_me:
            expiry_time = self.created_at + timedelta(days=30)
        else:
            expiry_time = self.last_activity + timedelta(minutes=30)
        return timezone.now() > expiry_time

class SessionStatistics(models.Model):
    date = models.DateField(unique=True)
    total_sessions = models.IntegerField(default=0)
    unique_users = models.IntegerField(default=0)
    peak_concurrent = models.IntegerField(default=0)
    avg_duration = models.DurationField(null=True, blank=True)
    mobile_sessions = models.IntegerField(default=0)
    desktop_sessions = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Session Statistics"
    
    def __str__(self):
        return f"Stats for {self.date}"
