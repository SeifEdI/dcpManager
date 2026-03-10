"""
Utility helpers for the maintenance module.
"""
from django.utils import timezone
from datetime import timedelta


def get_maintenance_dashboard_stats(days=30):
    """Return a dict of summary statistics for the maintenance dashboard."""
    from .models import Asset, WorkOrder, MaintenanceSchedule

    since = timezone.now() - timedelta(days=days)

    total_assets = Asset.objects.count()
    operational_assets = Asset.objects.filter(status='operational').count()
    assets_under_maintenance = Asset.objects.filter(status='under_maintenance').count()
    out_of_service_assets = Asset.objects.filter(status='out_of_service').count()

    open_work_orders = WorkOrder.objects.filter(status='open').count()
    in_progress_work_orders = WorkOrder.objects.filter(status='in_progress').count()
    completed_work_orders = WorkOrder.objects.filter(
        status='completed', completed_at__gte=since
    ).count()
    overdue_work_orders = WorkOrder.objects.filter(
        due_date__lt=timezone.now().date()
    ).exclude(status__in=['completed', 'cancelled']).count()

    urgent_work_orders = WorkOrder.objects.filter(
        priority='urgent'
    ).exclude(status__in=['completed', 'cancelled']).count()

    overdue_schedules = MaintenanceSchedule.objects.filter(
        is_active=True,
        next_due__lt=timezone.now().date(),
    ).count()

    upcoming_schedules = MaintenanceSchedule.objects.filter(
        is_active=True,
        next_due__gte=timezone.now().date(),
        next_due__lte=(timezone.now() + timedelta(days=7)).date(),
    ).count()

    return {
        'total_assets': total_assets,
        'operational_assets': operational_assets,
        'assets_under_maintenance': assets_under_maintenance,
        'out_of_service_assets': out_of_service_assets,
        'open_work_orders': open_work_orders,
        'in_progress_work_orders': in_progress_work_orders,
        'completed_work_orders': completed_work_orders,
        'overdue_work_orders': overdue_work_orders,
        'urgent_work_orders': urgent_work_orders,
        'overdue_schedules': overdue_schedules,
        'upcoming_schedules': upcoming_schedules,
    }


def update_schedule_next_due(schedule):
    """Recalculate and save the next_due date for a MaintenanceSchedule."""
    from datetime import date

    base = schedule.last_performed or date.today()
    interval = schedule.interval_days
    schedule.next_due = base + timedelta(days=interval)
    schedule.save(update_fields=['next_due'])


def complete_work_order(work_order, resolution_notes='', parts_used='', actual_hours=None):
    """
    Mark a WorkOrder as completed and create a MaintenanceLog entry.
    Returns the created MaintenanceLog instance.
    """
    from .models import MaintenanceLog

    work_order.status = 'completed'
    work_order.completed_at = timezone.now()
    if resolution_notes:
        work_order.resolution_notes = resolution_notes
    if parts_used:
        work_order.parts_used = parts_used
    if actual_hours is not None:
        work_order.actual_hours = actual_hours
    work_order.save()

    # Update asset status back to operational if it was under maintenance
    asset = work_order.asset
    if asset.status == 'under_maintenance':
        asset.status = 'operational'
        asset.save(update_fields=['status'])

    # Update linked schedule
    if work_order.schedule:
        schedule = work_order.schedule
        schedule.last_performed = timezone.now().date()
        update_schedule_next_due(schedule)

    log = MaintenanceLog.objects.create(
        work_order=work_order,
        asset=work_order.asset,
        performed_by=work_order.assigned_to,
        performed_at=work_order.completed_at,
        summary=resolution_notes or f"Work order {work_order.work_order_number} completed.",
    )
    return log


def get_asset_maintenance_history(asset, limit=20):
    """Return the most recent MaintenanceLog entries for an asset."""
    from .models import MaintenanceLog
    return MaintenanceLog.objects.filter(asset=asset).order_by('-performed_at')[:limit]


def get_overdue_work_orders():
    """Return all overdue (past due_date) open/in-progress work orders."""
    from .models import WorkOrder
    return WorkOrder.objects.filter(
        due_date__lt=timezone.now().date()
    ).exclude(status__in=['completed', 'cancelled']).select_related('asset', 'assigned_to')


def get_upcoming_schedules(days=7):
    """Return preventive maintenance schedules due within the next `days` days."""
    from .models import MaintenanceSchedule
    today = timezone.now().date()
    deadline = today + timedelta(days=days)
    return MaintenanceSchedule.objects.filter(
        is_active=True,
        next_due__gte=today,
        next_due__lte=deadline,
    ).select_related('asset', 'assigned_to').order_by('next_due')
