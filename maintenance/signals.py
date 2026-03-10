"""
Django signals for the maintenance module.

- When a WorkOrder status changes to 'in_progress', set the asset status to 'under_maintenance'.
- When a WorkOrder is completed or cancelled, restore the asset to 'operational' (if no other
  open work orders remain).
- When a MaintenanceSchedule's last_performed is updated, recalculate next_due.
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone


@receiver(pre_save, sender='maintenance.WorkOrder')
def work_order_pre_save(sender, instance, **kwargs):
    """Track status transitions and update timestamps."""
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            return

        # Mark started_at when transitioning to in_progress
        if old.status != 'in_progress' and instance.status == 'in_progress':
            if not instance.started_at:
                instance.started_at = timezone.now()

        # Mark completed_at when transitioning to completed
        if old.status != 'completed' and instance.status == 'completed':
            if not instance.completed_at:
                instance.completed_at = timezone.now()


@receiver(post_save, sender='maintenance.WorkOrder')
def work_order_post_save(sender, instance, created, **kwargs):
    """Sync asset status based on work order status."""
    asset = instance.asset

    if instance.status == 'in_progress':
        if asset.status == 'operational':
            asset.status = 'under_maintenance'
            asset.save(update_fields=['status'])

    elif instance.status in ('completed', 'cancelled'):
        # Only restore if no other open/in-progress work orders exist
        remaining = (
            sender.objects
            .filter(asset=asset)
            .exclude(pk=instance.pk)
            .exclude(status__in=['completed', 'cancelled'])
            .exists()
        )
        if not remaining and asset.status == 'under_maintenance':
            asset.status = 'operational'
            asset.save(update_fields=['status'])


@receiver(post_save, sender='maintenance.MaintenanceSchedule')
def schedule_post_save(sender, instance, created, **kwargs):
    """Recalculate next_due when last_performed changes."""
    if instance.last_performed and not created:
        from .utils import update_schedule_next_due
        # Avoid infinite recursion by checking if next_due is already correct
        from datetime import timedelta
        expected_next = instance.last_performed + timedelta(days=instance.interval_days)
        if instance.next_due != expected_next:
            update_schedule_next_due(instance)
