from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone

from rbac.decorators import rbac_required
from .models import Asset, AssetCategory, MaintenanceSchedule, WorkOrder, WorkOrderComment, MaintenanceLog, TechnicalDatasheet
from .forms import (
    AssetForm, AssetCategoryForm, MaintenanceScheduleForm,
    WorkOrderForm, WorkOrderCommentForm, MaintenanceLogForm,
    WorkOrderFilterForm, AssetFilterForm, TechnicalDatasheetForm,
)
from .utils import get_maintenance_dashboard_stats, get_overdue_work_orders, get_upcoming_schedules


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@rbac_required('maintenance.view', redirect_url='dashboard')
def dashboard(request):
    """Maintenance module overview dashboard."""
    days = int(request.GET.get('days', 30))
    stats = get_maintenance_dashboard_stats(days=days)

    recent_work_orders = WorkOrder.objects.select_related('asset', 'assigned_to').order_by('-created_at')[:10]
    overdue_work_orders = get_overdue_work_orders()[:5]
    upcoming_schedules = get_upcoming_schedules(days=7)

    # Work orders by status
    wo_by_status = (
        WorkOrder.objects.values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )

    # Assets by criticality
    assets_by_criticality = (
        Asset.objects.values('criticality')
        .annotate(count=Count('id'))
        .order_by('criticality')
    )

    context = {
        'title': 'Maintenance Dashboard',
        'days': days,
        **stats,
        'recent_work_orders': recent_work_orders,
        'overdue_work_orders_list': overdue_work_orders,
        'upcoming_schedules_list': upcoming_schedules,
        'wo_by_status': wo_by_status,
        'assets_by_criticality': assets_by_criticality,
    }
    return render(request, 'maintenance/dashboard.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# Assets
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@rbac_required('maintenance.view', redirect_url='dashboard')
def asset_list(request):
    """List all assets with filtering."""
    form = AssetFilterForm(request.GET or None)
    assets = Asset.objects.select_related('category', 'assigned_to').all()

    if form.is_valid():
        if form.cleaned_data.get('status'):
            assets = assets.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('criticality'):
            assets = assets.filter(criticality=form.cleaned_data['criticality'])
        if form.cleaned_data.get('category'):
            assets = assets.filter(category=form.cleaned_data['category'])
        if form.cleaned_data.get('search'):
            q = form.cleaned_data['search']
            assets = assets.filter(
                Q(asset_id__icontains=q) |
                Q(name__icontains=q) |
                Q(location__icontains=q) |
                Q(serial_number__icontains=q) |
                Q(manufacturer__icontains=q)
            )

    paginator = Paginator(assets, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'title': 'Assets',
        'page_obj': page_obj,
        'filter_form': form,
        'total_count': assets.count(),
    }
    return render(request, 'maintenance/asset_list.html', context)


@login_required
@rbac_required('maintenance.view', redirect_url='dashboard')
def asset_detail(request, pk):
    """Asset detail with maintenance history, open work orders, and datasheets."""
    asset = get_object_or_404(Asset, pk=pk)
    open_work_orders = asset.work_orders.exclude(status__in=['completed', 'cancelled']).order_by('-created_at')
    maintenance_logs = asset.maintenance_logs.order_by('-performed_at')[:10]
    schedules = asset.schedules.filter(is_active=True).order_by('next_due')
    datasheets = asset.datasheets.select_related('uploaded_by').order_by('-created_at')

    context = {
        'title': f'Asset: {asset.name}',
        'asset': asset,
        'open_work_orders': open_work_orders,
        'maintenance_logs': maintenance_logs,
        'schedules': schedules,
        'datasheets': datasheets,
    }
    return render(request, 'maintenance/asset_detail.html', context)


@login_required
@rbac_required('maintenance.manage', redirect_url='maintenance:asset_list')
def asset_create(request):
    """Create a new asset."""
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.created_by = request.user
            asset.save()
            messages.success(request, f'Asset "{asset.name}" created successfully.')
            return redirect('maintenance:asset_detail', pk=asset.pk)
    else:
        form = AssetForm()

    context = {'title': 'Add Asset', 'form': form, 'action': 'Create'}
    return render(request, 'maintenance/asset_form.html', context)


@login_required
@rbac_required('maintenance.manage', redirect_url='maintenance:asset_list')
def asset_edit(request, pk):
    """Edit an existing asset."""
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, f'Asset "{asset.name}" updated successfully.')
            return redirect('maintenance:asset_detail', pk=asset.pk)
    else:
        form = AssetForm(instance=asset)

    context = {'title': f'Edit Asset: {asset.name}', 'form': form, 'asset': asset, 'action': 'Update'}
    return render(request, 'maintenance/asset_form.html', context)


@login_required
@rbac_required('maintenance.manage', redirect_url='maintenance:asset_list')
def asset_delete(request, pk):
    """Delete an asset (POST only)."""
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        name = asset.name
        asset.delete()
        messages.success(request, f'Asset "{name}" deleted.')
        return redirect('maintenance:asset_list')
    context = {'title': f'Delete Asset: {asset.name}', 'asset': asset}
    return render(request, 'maintenance/asset_confirm_delete.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# Technical Datasheets
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@rbac_required('maintenance.manage', redirect_url='maintenance:asset_list')
def datasheet_upload(request, asset_pk):
    """Upload a technical datasheet for an asset."""
    asset = get_object_or_404(Asset, pk=asset_pk)
    if request.method == 'POST':
        form = TechnicalDatasheetForm(request.POST, request.FILES)
        if form.is_valid():
            datasheet = form.save(commit=False)
            datasheet.asset = asset
            datasheet.uploaded_by = request.user
            datasheet.save()
            messages.success(request, f'Datasheet "{datasheet.title}" uploaded successfully.')
            return redirect('maintenance:asset_detail', pk=asset_pk)
    else:
        form = TechnicalDatasheetForm()

    context = {
        'title': f'Upload Datasheet – {asset}',
        'form': form,
        'asset': asset,
    }
    return render(request, 'maintenance/datasheet_form.html', context)


@login_required
@rbac_required('maintenance.manage', redirect_url='maintenance:asset_list')
def datasheet_delete(request, pk):
    """Delete a technical datasheet (POST only)."""
    datasheet = get_object_or_404(TechnicalDatasheet, pk=pk)
    asset_pk = datasheet.asset.pk
    if request.method == 'POST':
        title = datasheet.title
        datasheet.file.delete(save=False)   # remove file from disk
        datasheet.delete()
        messages.success(request, f'Datasheet "{title}" deleted.')
    return redirect('maintenance:asset_detail', pk=asset_pk)


# ─────────────────────────────────────────────────────────────────────────────
# Work Orders
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@rbac_required('maintenance.view', redirect_url='dashboard')
def work_order_list(request):
    """List work orders with filtering."""
    form = WorkOrderFilterForm(request.GET or None)
    work_orders = WorkOrder.objects.select_related('asset', 'assigned_to', 'requested_by').all()

    if form.is_valid():
        if form.cleaned_data.get('status'):
            work_orders = work_orders.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('priority'):
            work_orders = work_orders.filter(priority=form.cleaned_data['priority'])
        if form.cleaned_data.get('work_type'):
            work_orders = work_orders.filter(work_type=form.cleaned_data['work_type'])
        if form.cleaned_data.get('search'):
            q = form.cleaned_data['search']
            work_orders = work_orders.filter(
                Q(work_order_number__icontains=q) |
                Q(title__icontains=q) |
                Q(asset__name__icontains=q) |
                Q(asset__asset_id__icontains=q)
            )
        if form.cleaned_data.get('date_from'):
            work_orders = work_orders.filter(created_at__date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            work_orders = work_orders.filter(created_at__date__lte=form.cleaned_data['date_to'])

    paginator = Paginator(work_orders, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'title': 'Work Orders',
        'page_obj': page_obj,
        'filter_form': form,
        'total_count': work_orders.count(),
    }
    return render(request, 'maintenance/work_order_list.html', context)


@login_required
@rbac_required('maintenance.view', redirect_url='dashboard')
def work_order_detail(request, pk):
    """Work order detail with comments."""
    work_order = get_object_or_404(
        WorkOrder.objects.select_related('asset', 'assigned_to', 'requested_by', 'schedule'),
        pk=pk,
    )
    comments = work_order.comments.select_related('author').all()
    comment_form = WorkOrderCommentForm()

    # Maintenance log if completed
    maintenance_log = getattr(work_order, 'maintenance_log', None)

    if request.method == 'POST' and 'add_comment' in request.POST:
        comment_form = WorkOrderCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.work_order = work_order
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added.')
            return redirect('maintenance:work_order_detail', pk=pk)

    context = {
        'title': f'Work Order: {work_order.work_order_number}',
        'work_order': work_order,
        'comments': comments,
        'comment_form': comment_form,
        'maintenance_log': maintenance_log,
    }
    return render(request, 'maintenance/work_order_detail.html', context)


@login_required
@rbac_required('maintenance.manage', redirect_url='maintenance:work_order_list')
def work_order_create(request):
    """Create a new work order."""
    initial = {}
    asset_pk = request.GET.get('asset')
    if asset_pk:
        initial['asset'] = asset_pk

    if request.method == 'POST':
        form = WorkOrderForm(request.POST)
        if form.is_valid():
            wo = form.save(commit=False)
            wo.requested_by = request.user
            wo.save()
            messages.success(request, f'Work order {wo.work_order_number} created.')
            return redirect('maintenance:work_order_detail', pk=wo.pk)
    else:
        form = WorkOrderForm(initial=initial)

    context = {'title': 'Create Work Order', 'form': form, 'action': 'Create'}
    return render(request, 'maintenance/work_order_form.html', context)


@login_required
@rbac_required('maintenance.manage', redirect_url='maintenance:work_order_list')
def work_order_edit(request, pk):
    """Edit an existing work order."""
    work_order = get_object_or_404(WorkOrder, pk=pk)
    if request.method == 'POST':
        form = WorkOrderForm(request.POST, instance=work_order)
        if form.is_valid():
            form.save()
            messages.success(request, f'Work order {work_order.work_order_number} updated.')
            return redirect('maintenance:work_order_detail', pk=pk)
    else:
        form = WorkOrderForm(instance=work_order)

    context = {
        'title': f'Edit Work Order: {work_order.work_order_number}',
        'form': form,
        'work_order': work_order,
        'action': 'Update',
    }
    return render(request, 'maintenance/work_order_form.html', context)


@login_required
@rbac_required('maintenance.manage', redirect_url='maintenance:work_order_list')
def work_order_complete(request, pk):
    """Mark a work order as completed and create a maintenance log."""
    work_order = get_object_or_404(WorkOrder, pk=pk)

    if work_order.status in ('completed', 'cancelled'):
        messages.warning(request, 'This work order is already closed.')
        return redirect('maintenance:work_order_detail', pk=pk)

    if request.method == 'POST':
        log_form = MaintenanceLogForm(request.POST)
        if log_form.is_valid():
            from .utils import complete_work_order
            log = complete_work_order(
                work_order,
                resolution_notes=work_order.resolution_notes,
                parts_used=work_order.parts_used,
                actual_hours=work_order.actual_hours,
            )
            # Update the auto-created log with the form data
            form_data = log_form.cleaned_data
            log.performed_by = form_data.get('performed_by', log.performed_by)
            log.performed_at = form_data.get('performed_at', log.performed_at)
            log.summary = form_data.get('summary') or log.summary
            log.findings = form_data.get('findings', log.findings)
            log.recommendations = form_data.get('recommendations', log.recommendations)
            log.next_maintenance_date = form_data.get('next_maintenance_date', log.next_maintenance_date)
            log.cost = form_data.get('cost', log.cost)
            log.save()
            messages.success(request, f'Work order {work_order.work_order_number} marked as completed.')
            return redirect('maintenance:work_order_detail', pk=pk)
    else:
        log_form = MaintenanceLogForm(initial={
            'performed_by': work_order.assigned_to,
            'performed_at': timezone.now(),
        })

    context = {
        'title': f'Complete Work Order: {work_order.work_order_number}',
        'work_order': work_order,
        'log_form': log_form,
    }
    return render(request, 'maintenance/work_order_complete.html', context)


@login_required
@rbac_required('maintenance.manage', redirect_url='maintenance:work_order_list')
def work_order_delete(request, pk):
    """Delete a work order (POST only)."""
    work_order = get_object_or_404(WorkOrder, pk=pk)
    if request.method == 'POST':
        number = work_order.work_order_number
        work_order.delete()
        messages.success(request, f'Work order {number} deleted.')
        return redirect('maintenance:work_order_list')
    context = {'title': f'Delete Work Order: {work_order.work_order_number}', 'work_order': work_order}
    return render(request, 'maintenance/work_order_confirm_delete.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# Maintenance Schedules
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@rbac_required('maintenance.view', redirect_url='dashboard')
def schedule_list(request):
    """List all maintenance schedules."""
    schedules = MaintenanceSchedule.objects.select_related('asset', 'assigned_to').all()

    active_only = request.GET.get('active_only', 'true')
    if active_only == 'true':
        schedules = schedules.filter(is_active=True)

    overdue_only = request.GET.get('overdue_only')
    if overdue_only:
        schedules = schedules.filter(next_due__lt=timezone.now().date())

    paginator = Paginator(schedules.order_by('next_due'), 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'title': 'Maintenance Schedules',
        'page_obj': page_obj,
        'active_only': active_only,
        'overdue_only': overdue_only,
    }
    return render(request, 'maintenance/schedule_list.html', context)


@login_required
@rbac_required('maintenance.manage', redirect_url='maintenance:schedule_list')
def schedule_create(request):
    """Create a new maintenance schedule."""
    if request.method == 'POST':
        form = MaintenanceScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user
            schedule.save()
            messages.success(request, f'Schedule "{schedule.title}" created.')
            return redirect('maintenance:schedule_list')
    else:
        form = MaintenanceScheduleForm()

    context = {'title': 'Create Maintenance Schedule', 'form': form, 'action': 'Create'}
    return render(request, 'maintenance/schedule_form.html', context)


@login_required
@rbac_required('maintenance.manage', redirect_url='maintenance:schedule_list')
def schedule_edit(request, pk):
    """Edit a maintenance schedule."""
    schedule = get_object_or_404(MaintenanceSchedule, pk=pk)
    if request.method == 'POST':
        form = MaintenanceScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, f'Schedule "{schedule.title}" updated.')
            return redirect('maintenance:schedule_list')
    else:
        form = MaintenanceScheduleForm(instance=schedule)

    context = {'title': f'Edit Schedule: {schedule.title}', 'form': form, 'schedule': schedule, 'action': 'Update'}
    return render(request, 'maintenance/schedule_form.html', context)


@login_required
@rbac_required('maintenance.manage', redirect_url='maintenance:schedule_list')
def schedule_delete(request, pk):
    """Delete a maintenance schedule."""
    schedule = get_object_or_404(MaintenanceSchedule, pk=pk)
    if request.method == 'POST':
        title = schedule.title
        schedule.delete()
        messages.success(request, f'Schedule "{title}" deleted.')
        return redirect('maintenance:schedule_list')
    context = {'title': f'Delete Schedule: {schedule.title}', 'schedule': schedule}
    return render(request, 'maintenance/schedule_confirm_delete.html', context)
