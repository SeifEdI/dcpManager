from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Employee, Department, Attendance

class EmployeeInline(admin.StackedInline):
    model = Employee
    can_delete = False
    verbose_name_plural = 'Employee Profile'

class UserAdmin(BaseUserAdmin):
    inlines = (EmployeeInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'full_name', 'employee_type', 'department', 'position', 'status']
    list_filter = ['employee_type', 'status', 'department', 'hire_date']
    search_fields = ['employee_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'employee_id', 'employee_type', 'status')
        }),
        ('Work Information', {
            'fields': ('department', 'position', 'hire_date')
        }),
        ('Contact Information', {
            'fields': ('phone_number',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'clock_in', 'clock_out', 'duration', 'created_by', 'created_at']
    list_filter = ['date', 'employee__department']
    search_fields = ['employee__employee_id', 'employee__user__username', 'employee__user__first_name', 'employee__user__last_name']
    readonly_fields = ['created_at', 'updated_at']
