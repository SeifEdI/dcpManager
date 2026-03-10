import os
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class AssetCategory(models.Model):
    """Category for grouping assets (e.g. Electrical, Mechanical, HVAC)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Asset Category'
        verbose_name_plural = 'Asset Categories'

    def __str__(self):
        return self.name


class Asset(models.Model):
    """Physical asset / equipment that can be maintained"""

    STATUS_CHOICES = [
        ('operational', 'Operational'),
        ('under_maintenance', 'Under Maintenance'),
        ('out_of_service', 'Out of Service'),
        ('decommissioned', 'Decommissioned'),
    ]

    CRITICALITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    asset_id = models.CharField(max_length=30, unique=True, help_text='Unique asset identifier')
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        AssetCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets',
    )
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True, help_text='Physical location of the asset')
    serial_number = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=100, blank=True)
    model_number = models.CharField(max_length=100, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='operational')
    criticality = models.CharField(max_length=10, choices=CRITICALITY_CHOICES, default='medium')
    assigned_to = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_assets',
        help_text='Employee responsible for this asset',
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_assets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['asset_id']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['criticality']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.asset_id} – {self.name}"

    @property
    def is_operational(self):
        return self.status == 'operational'

    @property
    def warranty_active(self):
        if self.warranty_expiry:
            return self.warranty_expiry >= timezone.now().date()
        return False

    @property
    def open_work_orders_count(self):
        return self.work_orders.exclude(status__in=['completed', 'cancelled']).count()


class MaintenanceSchedule(models.Model):
    """Preventive maintenance schedule for an asset"""

    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
        ('custom', 'Custom (days)'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='schedules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES, default='monthly')
    custom_interval_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Number of days between maintenance (used when frequency is "custom")',
    )
    last_performed = models.DateField(null=True, blank=True)
    next_due = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_schedules',
    )
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_due']
        indexes = [
            models.Index(fields=['next_due']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.asset} – {self.title} ({self.get_frequency_display()})"

    @property
    def is_overdue(self):
        if self.next_due:
            return self.next_due < timezone.now().date()
        return False

    @property
    def interval_days(self):
        """Return the interval in days based on frequency."""
        mapping = {
            'daily': 1,
            'weekly': 7,
            'monthly': 30,
            'quarterly': 90,
            'semi_annual': 180,
            'annual': 365,
            'custom': self.custom_interval_days or 30,
        }
        return mapping.get(self.frequency, 30)


class WorkOrder(models.Model):
    """Maintenance work order – corrective or preventive"""

    TYPE_CHOICES = [
        ('corrective', 'Corrective'),
        ('preventive', 'Preventive'),
        ('inspection', 'Inspection'),
        ('emergency', 'Emergency'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    work_order_number = models.CharField(max_length=30, unique=True, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    work_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='corrective')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='work_orders')
    schedule = models.ForeignKey(
        MaintenanceSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_orders',
        help_text='Linked preventive maintenance schedule (if any)',
    )

    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requested_work_orders',
    )
    assigned_to = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_work_orders',
    )

    due_date = models.DateField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    resolution_notes = models.TextField(blank=True, help_text='Notes on how the issue was resolved')
    parts_used = models.TextField(blank=True, help_text='List of parts / materials used')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['priority', '-created_at']),
            models.Index(fields=['asset', 'status']),
            models.Index(fields=['assigned_to', 'status']),
        ]

    def __str__(self):
        return f"{self.work_order_number} – {self.title}"

    def save(self, *args, **kwargs):
        if not self.work_order_number:
            self.work_order_number = self._generate_work_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_work_order_number():
        from django.utils import timezone as tz
        prefix = f"WO-{tz.now().strftime('%Y%m')}"
        last = (
            WorkOrder.objects.filter(work_order_number__startswith=prefix)
            .order_by('-work_order_number')
            .first()
        )
        if last:
            try:
                seq = int(last.work_order_number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}-{seq:04d}"

    @property
    def is_overdue(self):
        if self.due_date and self.status not in ('completed', 'cancelled'):
            return self.due_date < timezone.now().date()
        return False

    @property
    def duration(self):
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None


class WorkOrderComment(models.Model):
    """Comments / updates on a work order"""

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.work_order}"


# ─────────────────────────────────────────────────────────────────────────────
# Technical Datasheets
# ─────────────────────────────────────────────────────────────────────────────

def datasheet_upload_path(instance, filename):
    """Store datasheets under media/datasheets/<asset_id>/<filename>."""
    return f'datasheets/{instance.asset.asset_id}/{filename}'


class TechnicalDatasheet(models.Model):
    """Technical document / datasheet attached to an asset."""

    DOCUMENT_TYPE_CHOICES = [
        ('datasheet', 'Technical Datasheet'),
        ('manual', 'User Manual'),
        ('schematic', 'Schematic / Drawing'),
        ('certificate', 'Certificate'),
        ('warranty', 'Warranty Document'),
        ('other', 'Other'),
    ]

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='datasheets',
    )
    title = models.CharField(max_length=200)
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_TYPE_CHOICES,
        default='datasheet',
    )
    file = models.FileField(upload_to=datasheet_upload_path)
    version = models.CharField(max_length=50, blank=True, help_text='e.g. v1.0, Rev A')
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_datasheets',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Technical Datasheet'
        verbose_name_plural = 'Technical Datasheets'

    def __str__(self):
        return f"{self.title} ({self.asset.asset_id})"

    @property
    def filename(self):
        return os.path.basename(self.file.name) if self.file else ''

    @property
    def file_size_display(self):
        if self.file:
            try:
                size = self.file.size
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024:
                        return f"{size:.1f} {unit}"
                    size /= 1024
            except (OSError, FileNotFoundError):
                pass
        return '—'

    @property
    def file_extension(self):
        if self.file:
            _, ext = os.path.splitext(self.file.name)
            return ext.lower().lstrip('.')
        return ''


class MaintenanceLog(models.Model):
    """Historical log of completed maintenance activities"""

    work_order = models.OneToOneField(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='maintenance_log',
    )
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_logs')
    performed_by = models.ForeignKey(
        'employees.Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_logs',
    )
    performed_at = models.DateTimeField(default=timezone.now)
    summary = models.TextField()
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-performed_at']
        indexes = [
            models.Index(fields=['asset', '-performed_at']),
        ]

    def __str__(self):
        return f"Log for {self.work_order} – {self.performed_at.date()}"
