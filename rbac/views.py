from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import transaction
from django.core.paginator import Paginator
from .models import Role, Permission, UserRole
from .decorators import rbac_required
from .utils import RBACManager
from .forms import RoleForm, AssignRoleForm

@login_required
@rbac_required('users.manage', redirect_url='dashboard')
def role_list(request):
    """List all roles"""
    roles = Role.objects.prefetch_related('permissions', 'role_users').all()
    
    context = {
        'roles': roles,
        'title': 'Role Management',
    }
    return render(request, 'rbac/role_list.html', context)

@login_required
@rbac_required('users.manage', redirect_url='dashboard')
def role_detail(request, role_id):
    """View role details"""
    role = get_object_or_404(Role, id=role_id)
    users_with_role = UserRole.objects.filter(role=role, is_active=True).select_related('user')
    
    context = {
        'role': role,
        'users_with_role': users_with_role,
        'title': f'Role Details - {role.name}',
    }
    return render(request, 'rbac/role_detail.html', context)

@login_required
@rbac_required('users.assign_roles', redirect_url='dashboard')
def user_roles(request, user_id):
    """Manage user roles"""
    user = get_object_or_404(User, id=user_id)
    user_roles = UserRole.objects.filter(user=user, is_active=True).select_related('role')
    available_roles = Role.objects.filter(is_active=True).exclude(
        id__in=user_roles.values_list('role_id', flat=True)
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        role_id = request.POST.get('role_id')
        
        if action == 'assign' and role_id:
            try:
                role = Role.objects.get(id=role_id, is_active=True)
                RBACManager.assign_role_to_user(user, role.name, request.user)
                messages.success(request, f'Role "{role.name}" assigned to {user.get_full_name() or user.username}')
            except Role.DoesNotExist:
                messages.error(request, 'Role not found')
        
        elif action == 'remove' and role_id:
            try:
                role = Role.objects.get(id=role_id)
                RBACManager.remove_role_from_user(user, role.name)
                messages.success(request, f'Role "{role.name}" removed from {user.get_full_name() or user.username}')
            except Role.DoesNotExist:
                messages.error(request, 'Role not found')
        
        return redirect('rbac:user_roles', user_id=user.id)
    
    context = {
        'target_user': user,
        'user_roles': user_roles,
        'available_roles': available_roles,
        'title': f'Manage Roles - {user.get_full_name() or user.username}',
    }
    return render(request, 'rbac/user_roles.html', context)

@login_required
@rbac_required('users.view', redirect_url='dashboard')
def user_list(request):
    """List all users with their roles"""
    users = User.objects.prefetch_related('user_roles__role').all()
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        users = users.filter(
            models.Q(username__icontains=search_query) |
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query) |
            models.Q(email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'title': 'User Management',
        'can_assign_roles': request.user.has_rbac_permission('users.assign_roles'),
    }
    return render(request, 'rbac/user_list.html', context)

@login_required
def my_permissions(request):
    """View current user's permissions"""
    permissions_summary = RBACManager.get_user_permissions_summary(request.user)
    user_roles = request.user.get_user_roles()
    
    context = {
        'permissions_summary': permissions_summary,
        'user_roles': user_roles,
        'title': 'My Permissions',
    }
    return render(request, 'rbac/my_permissions.html', context)
