import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employees', '0002_attendance'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AssetCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Asset Category',
                'verbose_name_plural': 'Asset Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asset_id', models.CharField(help_text='Unique asset identifier', max_length=30, unique=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('location', models.CharField(blank=True, help_text='Physical location of the asset', max_length=200)),
                ('serial_number', models.CharField(blank=True, max_length=100)),
                ('manufacturer', models.CharField(blank=True, max_length=100)),
                ('model_number', models.CharField(blank=True, max_length=100)),
                ('purchase_date', models.DateField(blank=True, null=True)),
                ('warranty_expiry', models.DateField(blank=True, null=True)),
                ('status', models.CharField(
                    choices=[
                        ('operational', 'Operational'),
                        ('under_maintenance', 'Under Maintenance'),
                        ('out_of_service', 'Out of Service'),
                        ('decommissioned', 'Decommissioned'),
                    ],
                    default='operational',
                    max_length=20,
                )),
                ('criticality', models.CharField(
                    choices=[
                        ('low', 'Low'),
                        ('medium', 'Medium'),
                        ('high', 'High'),
                        ('critical', 'Critical'),
                    ],
                    default='medium',
                    max_length=10,
                )),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assets',
                    to='maintenance.assetcategory',
                )),
                ('assigned_to', models.ForeignKey(
                    blank=True,
                    help_text='Employee responsible for this asset',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assigned_assets',
                    to='employees.employee',
                )),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_assets',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['asset_id'],
            },
        ),
        migrations.AddIndex(
            model_name='asset',
            index=models.Index(fields=['status'], name='maintenance_asset_status_idx'),
        ),
        migrations.AddIndex(
            model_name='asset',
            index=models.Index(fields=['criticality'], name='maintenance_asset_criticality_idx'),
        ),
        migrations.AddIndex(
            model_name='asset',
            index=models.Index(fields=['category'], name='maintenance_asset_category_idx'),
        ),
        migrations.CreateModel(
            name='MaintenanceSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('frequency', models.CharField(
                    choices=[
                        ('daily', 'Daily'),
                        ('weekly', 'Weekly'),
                        ('monthly', 'Monthly'),
                        ('quarterly', 'Quarterly'),
                        ('semi_annual', 'Semi-Annual'),
                        ('annual', 'Annual'),
                        ('custom', 'Custom (days)'),
                    ],
                    default='monthly',
                    max_length=15,
                )),
                ('custom_interval_days', models.PositiveIntegerField(
                    blank=True,
                    help_text='Number of days between maintenance (used when frequency is "custom")',
                    null=True,
                )),
                ('last_performed', models.DateField(blank=True, null=True)),
                ('next_due', models.DateField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('asset', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='schedules',
                    to='maintenance.asset',
                )),
                ('assigned_to', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='maintenance_schedules',
                    to='employees.employee',
                )),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['next_due'],
            },
        ),
        migrations.AddIndex(
            model_name='maintenanceschedule',
            index=models.Index(fields=['next_due'], name='maintenance_schedule_next_due_idx'),
        ),
        migrations.AddIndex(
            model_name='maintenanceschedule',
            index=models.Index(fields=['is_active'], name='maintenance_schedule_active_idx'),
        ),
        migrations.CreateModel(
            name='WorkOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('work_order_number', models.CharField(editable=False, max_length=30, unique=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('work_type', models.CharField(
                    choices=[
                        ('corrective', 'Corrective'),
                        ('preventive', 'Preventive'),
                        ('inspection', 'Inspection'),
                        ('emergency', 'Emergency'),
                    ],
                    default='corrective',
                    max_length=15,
                )),
                ('priority', models.CharField(
                    choices=[
                        ('low', 'Low'),
                        ('medium', 'Medium'),
                        ('high', 'High'),
                        ('urgent', 'Urgent'),
                    ],
                    default='medium',
                    max_length=10,
                )),
                ('status', models.CharField(
                    choices=[
                        ('open', 'Open'),
                        ('in_progress', 'In Progress'),
                        ('on_hold', 'On Hold'),
                        ('completed', 'Completed'),
                        ('cancelled', 'Cancelled'),
                    ],
                    default='open',
                    max_length=15,
                )),
                ('due_date', models.DateField(blank=True, null=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('estimated_hours', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('actual_hours', models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ('resolution_notes', models.TextField(blank=True, help_text='Notes on how the issue was resolved')),
                ('parts_used', models.TextField(blank=True, help_text='List of parts / materials used')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('asset', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='work_orders',
                    to='maintenance.asset',
                )),
                ('schedule', models.ForeignKey(
                    blank=True,
                    help_text='Linked preventive maintenance schedule (if any)',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='work_orders',
                    to='maintenance.maintenanceschedule',
                )),
                ('assigned_to', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='assigned_work_orders',
                    to='employees.employee',
                )),
                ('requested_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='requested_work_orders',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='workorder',
            index=models.Index(fields=['status', '-created_at'], name='maintenance_wo_status_idx'),
        ),
        migrations.AddIndex(
            model_name='workorder',
            index=models.Index(fields=['priority', '-created_at'], name='maintenance_wo_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='workorder',
            index=models.Index(fields=['asset', 'status'], name='maintenance_wo_asset_status_idx'),
        ),
        migrations.AddIndex(
            model_name='workorder',
            index=models.Index(fields=['assigned_to', 'status'], name='maintenance_wo_assigned_idx'),
        ),
        migrations.CreateModel(
            name='WorkOrderComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('work_order', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comments',
                    to='maintenance.workorder',
                )),
                ('author', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='MaintenanceLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('performed_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('summary', models.TextField()),
                ('findings', models.TextField(blank=True)),
                ('recommendations', models.TextField(blank=True)),
                ('next_maintenance_date', models.DateField(blank=True, null=True)),
                ('cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('work_order', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='maintenance_log',
                    to='maintenance.workorder',
                )),
                ('asset', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='maintenance_logs',
                    to='maintenance.asset',
                )),
                ('performed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='maintenance_logs',
                    to='employees.employee',
                )),
            ],
            options={
                'ordering': ['-performed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='maintenancelog',
            index=models.Index(fields=['asset', '-performed_at'], name='maintenance_log_asset_idx'),
        ),
    ]
