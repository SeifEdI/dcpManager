from django.contrib import admin
from django.utils.html import format_html
from .models import AssetCategory, Asset, MaintenanceSchedule, WorkOrder, WorkOrderComment, MaintenanceLog, TechnicalDatasheet


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']


class TechnicalDatasheetInline(admin.TabularInline):
    model = TechnicalDatasheet
    extra = 1
    readonly_fields = ['created_at', 'uploaded_by', 'file_size_display']
    fields = ['title', 'document_type', 'file', 'version', 'description', 'uploaded_by', 'created_at']

    def file_size_display(self, obj):
        return obj.file_size_display if obj.pk else '—'
    file_size_display.short_description = 'File Size'


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    inlines = [TechnicalDatasheetInline]
    list_display = [
        'asset_id', 'name', 'category', 'location', 'status_badge',
        'criticality', 'assigned_to', 'warranty_active_display',
    ]
    list_filter = ['status', 'criticality', 'category']
    search_fields = ['asset_id', 'name', 'serial_number', 'location', 'manufacturer']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Identification', {
            'fields': ('asset_id', 'name', 'category', 'description'),
        }),
        ('Technical Details', {
            'fields': ('serial_number', 'manufacturer', 'model_number'),
        }),
        ('Location & Assignment', {
            'fields': ('location', 'assigned_to'),
        }),
        ('Status & Criticality', {
            'fields': ('status', 'criticality'),
        }),
        ('Dates', {
            'fields': ('purchase_date', 'warranty_expiry'),
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        colours = {
            'operational': 'green',
            'under_maintenance': 'orange',
            'out_of_service': 'red',
            'decommissioned': 'grey',
        }
        colour = colours.get(obj.status, 'grey')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colour,
            obj.get_status_display(),
        )
    status_badge.short_description = 'Status'

    def warranty_active_display(self, obj):
        if obj.warranty_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Expired / N/A</span>')
    warranty_active_display.short_description = 'Warranty'


class WorkOrderCommentInline(admin.TabularInline):
    model = WorkOrderComment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ['title', 'asset', 'frequency', 'last_performed', 'next_due', 'overdue_display', 'is_active']
    list_filter = ['frequency', 'is_active']
    search_fields = ['title', 'asset__name', 'asset__asset_id']
    readonly_fields = ['created_at', 'updated_at']

    def overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">⚠ Overdue</span>')
        return format_html('<span style="color: green;">On Track</span>')
    overdue_display.short_description = 'Due Status'


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = [
        'work_order_number', 'title', 'asset', 'work_type', 'priority_badge',
        'status_badge', 'assigned_to', 'due_date', 'overdue_display',
    ]
    list_filter = ['status', 'priority', 'work_type']
    search_fields = ['work_order_number', 'title', 'asset__name', 'asset__asset_id']
    readonly_fields = ['work_order_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    inlines = [WorkOrderCommentInline]

    fieldsets = (
        ('Work Order Info', {
            'fields': ('work_order_number', 'title', 'description', 'work_type', 'priority', 'status'),
        }),
        ('Asset & Schedule', {
            'fields': ('asset', 'schedule'),
        }),
        ('Assignment', {
            'fields': ('requested_by', 'assigned_to'),
        }),
        ('Dates & Time', {
            'fields': ('due_date', 'started_at', 'completed_at', 'estimated_hours', 'actual_hours'),
        }),
        ('Resolution', {
            'fields': ('resolution_notes', 'parts_used'),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def priority_badge(self, obj):
        colours = {
            'low': '#6c757d',
            'medium': '#0d6efd',
            'high': '#fd7e14',
            'urgent': '#dc3545',
        }
        colour = colours.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colour,
            obj.get_priority_display(),
        )
    priority_badge.short_description = 'Priority'

    def status_badge(self, obj):
        colours = {
            'open': '#0d6efd',
            'in_progress': '#fd7e14',
            'on_hold': '#6c757d',
            'completed': '#198754',
            'cancelled': '#dc3545',
        }
        colour = colours.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colour,
            obj.get_status_display(),
        )
    status_badge.short_description = 'Status'

    def overdue_display(self, obj):
        if obj.is_overdue:
            return format_html('<span style="color: red; font-weight: bold;">⚠ Overdue</span>')
        return '—'
    overdue_display.short_description = 'Overdue'


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ['work_order', 'asset', 'performed_by', 'performed_at', 'cost']
    list_filter = ['performed_at']
    search_fields = ['work_order__work_order_number', 'asset__name', 'summary']
    readonly_fields = ['created_at']
    date_hierarchy = 'performed_at'

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(TechnicalDatasheet)
class TechnicalDatasheetAdmin(admin.ModelAdmin):
    list_display = ['title', 'asset', 'document_type', 'version', 'file_size_display', 'uploaded_by', 'created_at']
    list_filter = ['document_type', 'created_at']
    search_fields = ['title', 'asset__name', 'asset__asset_id', 'description']
    readonly_fields = ['created_at', 'updated_at', 'uploaded_by']
    date_hierarchy = 'created_at'

    def file_size_display(self, obj):
        return obj.file_size_display
    file_size_display.short_description = 'File Size'
