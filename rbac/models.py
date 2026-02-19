from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Permission(models.Model):
    """Custom permission model for fine-grained access control"""
    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    module = models.CharField(max_length=50, help_text="Module this permission belongs to (e.g., employees, dashboard)")
    
    class Meta:
        ordering = ['module', 'name']
    
    def __str__(self):
        return f"{self.module}.{self.codename}"

class Role(models.Model):
    """Role model that groups permissions"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_permission_list(self):
        """Get list of permission codenames for this role"""
        return list(self.permissions.values_list('codename', flat=True))

class UserRole(models.Model):
    """Many-to-many relationship between users and roles"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_users')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_roles')
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'role']
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"

# Add methods to User model
def user_has_permission(self, permission_codename):
    """Check if user has a specific permission through their roles"""
    if self.is_superuser:
        return True
    
    return self.user_roles.filter(
        is_active=True,
        role__is_active=True,
        role__permissions__codename=permission_codename
    ).exists()

def user_get_permissions(self):
    """Get all permissions for this user through their roles"""
    if self.is_superuser:
        return Permission.objects.all()
    
    return Permission.objects.filter(
        role__role_users__user=self,
        role__role_users__is_active=True,
        role__is_active=True
    ).distinct()

def user_get_roles(self):
    """Get all active roles for this user"""
    return Role.objects.filter(
        role_users__user=self,
        role_users__is_active=True,
        is_active=True
    )

# Add methods to User model
User.add_to_class('has_rbac_permission', user_has_permission)
User.add_to_class('get_rbac_permissions', user_get_permissions)
User.add_to_class('get_user_roles', user_get_roles)
