from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

def rbac_required(permission_codename, redirect_url=None):
    """
    Decorator to check if user has specific RBAC permission
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.has_rbac_permission(permission_codename):
                if redirect_url:
                    messages.error(request, f'You do not have permission to access this feature. Required permission: {permission_codename}')
                    return redirect(redirect_url)
                else:
                    raise PermissionDenied(f'Permission required: {permission_codename}')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def any_rbac_required(*permission_codenames, redirect_url=None):
    """
    Decorator to check if user has any of the specified RBAC permissions
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            has_permission = any(
                request.user.has_rbac_permission(perm) 
                for perm in permission_codenames
            )
            
            if not has_permission:
                if redirect_url:
                    messages.error(request, f'You do not have permission to access this feature.')
                    return redirect(redirect_url)
                else:
                    raise PermissionDenied('Insufficient permissions')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def all_rbac_required(*permission_codenames, redirect_url=None):
    """
    Decorator to check if user has all of the specified RBAC permissions
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            has_all_permissions = all(
                request.user.has_rbac_permission(perm) 
                for perm in permission_codenames
            )
            
            if not has_all_permissions:
                if redirect_url:
                    messages.error(request, f'You do not have sufficient permissions to access this feature.')
                    return redirect(redirect_url)
                else:
                    raise PermissionDenied('Insufficient permissions')
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
