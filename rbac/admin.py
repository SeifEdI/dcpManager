from django.contrib import admin
from .models import Permission, Role, UserRole

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename', 'module', 'description']
    list_filter = ['module']
    search_fields = ['name', 'codename', 'description']
    ordering = ['module', 'name']

class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 1
    readonly_fields = ['assigned_at']

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'permission_count', 'user_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['permissions']
    inlines = [UserRoleInline]
    
    def permission_count(self, obj):
        return obj.permissions.count()
    permission_count.short_description = 'Permissions'
    
    def user_count(self, obj):
        return obj.role_users.filter(is_active=True).count()
    user_count.short_description = 'Active Users'

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'assigned_by', 'assigned_at', 'is_active']
    list_filter = ['is_active', 'assigned_at', 'role']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'role__name']
    readonly_fields = ['assigned_at']
