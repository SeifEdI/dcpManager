from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.urls import reverse
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.utils import timezone
from .models import Employee, Department
from .forms import EmployeeProfileForm, AddEmployeeForm
from django.db import models
from rbac.decorators import rbac_required, any_rbac_required
from audit.utils import AuditLogger, AuditDecorator
import csv
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

@login_required
@rbac_required('employees.view', redirect_url='dashboard')
@AuditDecorator.log_employee_access('list_view')
def employee_list(request):
    """List all employees with pagination and filters"""
    employees = Employee.objects.select_related('user', 'department').all()
    
    # Filter by employee type if specified
    employee_type = request.GET.get('type')
    if employee_type in ['internal', 'external']:
        employees = employees.filter(employee_type=employee_type)
    
    # Filter by status if specified
    status = request.GET.get('status')
    if status in ['active', 'inactive', 'suspended']:
        employees = employees.filter(status=status)
    
    # Filter by department if specified
    department_id = request.GET.get('department')
    if department_id:
        employees = employees.filter(department_id=department_id)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        employees = employees.filter(
            models.Q(employee_id__icontains=search_query) |
            models.Q(user__first_name__icontains=search_query) |
            models.Q(user__last_name__icontains=search_query) |
            models.Q(user__username__icontains=search_query) |
            models.Q(position__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(employees, 10)  # Show 10 employees per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all departments for filter dropdown
    departments = Department.objects.all()
    
    context = {
        'page_obj': page_obj,
        'employees': page_obj,  # For backward compatibility
        'departments': departments,
        'title': 'Employee List',
        'current_type': employee_type,
        'current_status': status,
        'current_department': department_id,
        'search_query': search_query,
        'can_add_employee': request.user.has_rbac_permission('employees.add'),
        'can_edit_employee': request.user.has_rbac_permission('employees.edit'),
        'can_export_employee': request.user.has_rbac_permission('employees.export'),
        'can_view_sensitive': request.user.has_rbac_permission('employees.view_sensitive'),
    }
    return render(request, 'employees/list.html', context)

@login_required
@rbac_required('employees.export', redirect_url='employees:list')
def export_employees_csv(request):
    """Export employees to CSV file"""
    # Get the same filtered queryset as the list view
    employees = Employee.objects.select_related('user', 'department').all()
    
    # Apply the same filters as the list view
    employee_type = request.GET.get('type')
    if employee_type in ['internal', 'external']:
        employees = employees.filter(employee_type=employee_type)
    
    status = request.GET.get('status')
    if status in ['active', 'inactive', 'suspended']:
        employees = employees.filter(status=status)
    
    department_id = request.GET.get('department')
    if department_id:
        employees = employees.filter(department_id=department_id)
    
    search_query = request.GET.get('search')
    if search_query:
        employees = employees.filter(
            models.Q(employee_id__icontains=search_query) |
            models.Q(user__first_name__icontains=search_query) |
            models.Q(user__last_name__icontains=search_query) |
            models.Q(user__username__icontains=search_query) |
            models.Q(position__icontains=search_query)
        )
    
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="employees_export_{timestamp}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Check if user can view sensitive information
    can_view_sensitive = request.user.has_rbac_permission('employees.view_sensitive')
    
    # Write header row
    if can_view_sensitive:
        writer.writerow([
            'Employee ID',
            'Full Name',
            'Username',
            'Email',
            'Employee Type',
            'Department',
            'Position',
            'Status',
            'Phone Number',
            'Hire Date',
            'Created Date',
            'Last Updated'
        ])
    else:
        writer.writerow([
            'Employee ID',
            'Full Name',
            'Employee Type',
            'Department',
            'Position',
            'Status',
            'Hire Date'
        ])
    
    # Write data rows
    for employee in employees:
        if can_view_sensitive:
            writer.writerow([
                employee.employee_id,
                employee.full_name,
                employee.user.username,
                employee.user.email,
                employee.get_employee_type_display(),
                employee.department.name if employee.department else 'N/A',
                employee.position or 'N/A',
                employee.get_status_display(),
                employee.phone_number or 'N/A',
                employee.hire_date.strftime('%Y-%m-%d') if employee.hire_date else 'N/A',
                employee.created_at.strftime('%Y-%m-%d %H:%M'),
                employee.updated_at.strftime('%Y-%m-%d %H:%M')
            ])
        else:
            writer.writerow([
                employee.employee_id,
                employee.full_name,
                employee.get_employee_type_display(),
                employee.department.name if employee.department else 'N/A',
                employee.position or 'N/A',
                employee.get_status_display(),
                employee.hire_date.strftime('%Y-%m-%d') if employee.hire_date else 'N/A'
            ])
    
    # Log the export action
    AuditLogger.log_action(
        user=request.user,
        action='export',
        description=f'Exported {employees.count()} employees to CSV',
        request=request,
        severity='medium',
        module='employees',
        metadata={
            'export_format': 'csv',
            'records_count': employees.count(),
            'filters_applied': {
                'type': employee_type,
                'status': status,
                'department': department_id,
                'search': search_query
            }
        }
    )
    
    return response

@login_required
@rbac_required('employees.view', redirect_url='employees:list')
def print_employees_pdf(request):
    """Generate PDF for printing employees"""
    # Get the same filtered queryset as the list view
    employees = Employee.objects.select_related('user', 'department').all()
    
    # Apply the same filters as the list view
    employee_type = request.GET.get('type')
    if employee_type in ['internal', 'external']:
        employees = employees.filter(employee_type=employee_type)
    
    status = request.GET.get('status')
    if status in ['active', 'inactive', 'suspended']:
        employees = employees.filter(status=status)
    
    department_id = request.GET.get('department')
    if department_id:
        employees = employees.filter(department_id=department_id)
    
    search_query = request.GET.get('search')
    if search_query:
        employees = employees.filter(
            models.Q(employee_id__icontains=search_query) |
            models.Q(user__first_name__icontains=search_query) |
            models.Q(user__last_name__icontains=search_query) |
            models.Q(user__username__icontains=search_query) |
            models.Q(position__icontains=search_query)
        )
    
    # Create the HttpResponse object with PDF header
    response = HttpResponse(content_type='application/pdf')
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'inline; filename="employees_report_{timestamp}.pdf"'
    
    # Create PDF document
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center alignment
        textColor=colors.HexColor('#2c3e50')
    )
    
    # Add title
    title = Paragraph("dcpManager - Employee Report", title_style)
    elements.append(title)
    
    # Add generation info
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=20,
        alignment=1,  # Center alignment
        textColor=colors.HexColor('#7f8c8d')
    )
    
    generation_info = f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}<br/>"
    generation_info += f"Generated by: {request.user.get_full_name() or request.user.username}<br/>"
    generation_info += f"Total Records: {employees.count()}"
    
    info_para = Paragraph(generation_info, info_style)
    elements.append(info_para)
    elements.append(Spacer(1, 20))
    
    # Check if user can view sensitive information
    can_view_sensitive = request.user.has_rbac_permission('employees.view_sensitive')
    
    # Create table data
    if can_view_sensitive:
        table_data = [
            ['ID', 'Name', 'Type', 'Department', 'Position', 'Status', 'Phone', 'Email']
        ]
    else:
        table_data = [
            ['ID', 'Name', 'Type', 'Department', 'Position', 'Status']
        ]
    
    # Add employee data
    for employee in employees:
        if can_view_sensitive:
            row = [
                employee.employee_id,
                employee.full_name,
                employee.get_employee_type_display(),
                employee.department.name if employee.department else 'N/A',
                employee.position or 'N/A',
                employee.get_status_display(),
                employee.phone_number or 'N/A',
                employee.user.email or 'N/A'
            ]
        else:
            row = [
                employee.employee_id,
                employee.full_name,
                employee.get_employee_type_display(),
                employee.department.name if employee.department else 'N/A',
                employee.position or 'N/A',
                employee.get_status_display()
            ]
        table_data.append(row)
    
    # Create table
    if can_view_sensitive:
        col_widths = [0.8*inch, 1.5*inch, 1*inch, 1.2*inch, 1.2*inch, 0.8*inch, 1*inch, 1.5*inch]
    else:
        col_widths = [1*inch, 2*inch, 1.2*inch, 1.5*inch, 1.5*inch, 1*inch]
    
    table = Table(table_data, colWidths=col_widths)
    
    # Style the table
    table.setStyle(TableStyle([
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows styling
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        
        # Grid styling
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    elements.append(table)
    
    # Add footer
    elements.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=8,
        alignment=1,  # Center alignment
        textColor=colors.HexColor('#95a5a6')
    )
    
    footer_text = "This report is confidential and intended for authorized personnel only."
    footer_para = Paragraph(footer_text, footer_style)
    elements.append(footer_para)
    
    # Build PDF
    doc.build(elements)
    
    # Log the print action
    AuditLogger.log_action(
        user=request.user,
        action='print',
        description=f'Generated PDF report for {employees.count()} employees',
        request=request,
        severity='low',
        module='employees',
        metadata={
            'export_format': 'pdf',
            'records_count': employees.count(),
            'filters_applied': {
                'type': employee_type,
                'status': status,
                'department': department_id,
                'search': search_query
            }
        }
    )
    
    return response

@login_required
@rbac_required('employees.add', redirect_url='employees:list')
def add_employee(request):
    """Add a new employee"""
    if request.method == 'POST':
        form = AddEmployeeForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create user account
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password1'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        is_staff=form.cleaned_data['is_staff']
                    )
                    
                    # Create employee profile
                    employee = Employee.objects.create(
                        user=user,
                        employee_id=form.cleaned_data['employee_id'],
                        employee_type=form.cleaned_data['employee_type'],
                        department=form.cleaned_data['department'],
                        position=form.cleaned_data['position'],
                        phone_number=form.cleaned_data['phone_number'],
                        hire_date=form.cleaned_data['hire_date'],
                        status=form.cleaned_data['status']
                    )
                    
                    # Assign default role based on employee type
                    from rbac.utils import RBACManager
                    if form.cleaned_data['employee_type'] == 'internal':
                        RBACManager.assign_role_to_user(user, 'Employee', request.user)
                    else:
                        RBACManager.assign_role_to_user(user, 'Viewer', request.user)
                    
                    # Log the creation
                    AuditLogger.log_action(
                        user=request.user,
                        action='create',
                        description=f'Created new employee: {employee.full_name} (ID: {employee.employee_id})',
                        obj=employee,
                        request=request,
                        severity='medium',
                        module='employees',
                        metadata={
                            'employee_type': employee.employee_type,
                            'department': employee.department.name if employee.department else None,
                            'created_user_account': True
                        }
                    )
                    
                    messages.success(
                        request, 
                        f'Employee {employee.employee_id} - {employee.full_name} has been successfully created.'
                    )
                    return redirect('employees:detail', employee_id=employee.id)
                    
            except Exception as e:
                # Log the error
                AuditLogger.log_action(
                    user=request.user,
                    action='create',
                    description=f'Failed to create employee: {str(e)}',
                    request=request,
                    severity='high',
                    module='employees',
                    metadata={'error': str(e), 'form_data': form.cleaned_data}
                )
                messages.error(request, f'Error creating employee: {str(e)}')
    else:
        form = AddEmployeeForm()
    
    context = {
        'form': form,
        'title': 'Add New Employee',
    }
    return render(request, 'employees/add.html', context)

@login_required
@rbac_required('employees.view', redirect_url='dashboard')
def employee_detail(request, employee_id):
    """View employee details"""
    employee = get_object_or_404(Employee, id=employee_id)
    
    # Log the access
    AuditLogger.log_employee_access(
        user=request.user,
        access_type='detail_view',
        employee=employee,
        request=request
    )
    
    # Check if user can view sensitive information
    can_view_sensitive = request.user.has_rbac_permission('employees.view_sensitive')
    
    context = {
        'employee': employee,
        'title': f'Employee Details - {employee.full_name}',
        'can_edit': request.user.has_rbac_permission('employees.edit'),
        'can_view_sensitive': can_view_sensitive,
    }
    return render(request, 'employees/detail.html', context)

@login_required
def employee_profile(request):
    """View current user's employee profile"""
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')
    
    # Log the profile access
    AuditLogger.log_employee_access(
        user=request.user,
        access_type='profile_view',
        employee=employee,
        request=request
    )
    
    context = {
        'employee': employee,
        'title': 'My Profile',
    }
    return render(request, 'employees/profile.html', context)

@login_required
def edit_profile(request):
    """Edit current user's employee profile"""
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        messages.error(request, 'Employee profile not found.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = EmployeeProfileForm(request.POST, instance=employee, user=request.user)
        if form.is_valid():
            # Track changes for audit log
            changes = {}
            for field in form.changed_data:
                if hasattr(employee, field):
                    old_value = getattr(employee, field)
                    new_value = form.cleaned_data[field]
                    changes[field] = {'old': str(old_value), 'new': str(new_value)}
                elif field in ['first_name', 'last_name', 'email']:
                    old_value = getattr(request.user, field)
                    new_value = form.cleaned_data[field]
                    changes[field] = {'old': str(old_value), 'new': str(new_value)}
            
            with transaction.atomic():
                # Update user information
                user = request.user
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.email = form.cleaned_data['email']
                user.save()
                
                # Update employee profile
                form.save()
                
                # Log the update
                AuditLogger.log_action(
                    user=request.user,
                    action='update',
                    description=f'Updated own profile: {employee.full_name}',
                    obj=employee,
                    changes=changes,
                    request=request,
                    severity='low',
                    module='employees'
                )
                
            messages.success(request, 'Profile updated successfully.')
            return redirect('employees:profile')
    else:
        form = EmployeeProfileForm(instance=employee, user=request.user)
    
    context = {
        'form': form,
        'employee': employee,
        'title': 'Edit Profile',
    }
    return render(request, 'employees/edit_profile.html', context)
