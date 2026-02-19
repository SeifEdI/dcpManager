from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views, logout
from django.contrib import messages
from django.urls import reverse_lazy
from .forms import CustomAuthenticationForm
from .utils import SessionManager
from rbac.decorators import rbac_required

class LoginView(auth_views.LoginView):
    """Custom login view with Remember Me functionality"""
    template_name = 'registration/login.html'
    form_class = CustomAuthenticationForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('dashboard')
    
    def form_valid(self, form):
        # Call the parent form_valid method first
        response = super().form_valid(form)
        
        # Handle remember me functionality
        remember_me = form.cleaned_data.get('remember_me')
        
        if remember_me:
            SessionManager.set_remember_me_session(self.request)
            messages.success(
                self.request, 
                f'Welcome back, {self.request.user.get_full_name() or self.request.user.username}! '
                f'You will stay logged in for 30 days.'
            )
        else:
            SessionManager.set_regular_session(self.request)
            messages.success(
                self.request, 
                f'Welcome back, {self.request.user.get_full_name() or self.request.user.username}!'
            )
        
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)

def home(request):
    """Home page - redirect to dashboard if authenticated, otherwise show login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

@login_required
@rbac_required('dashboard.view', redirect_url='login')
def dashboard(request):
    """Main dashboard for authenticated users"""
    # Get user's roles and permissions for display
    user_roles = request.user.get_user_roles()
    
    context = {
        'user': request.user,
        'user_roles': user_roles,
        'title': 'dcpManager Dashboard',
        'can_view_employees': request.user.has_rbac_permission('employees.view'),
        'can_manage_users': request.user.has_rbac_permission('users.manage'),
        'can_view_analytics': request.user.has_rbac_permission('dashboard.view_analytics'),
    }
    return render(request, 'dashboard.html', context)

@login_required
def session_management(request):
    """Session management page"""
    context = {
        'title': 'Session Management'
    }
    return render(request, 'session_management.html', context)

def custom_logout(request):
    """Custom logout view with success message"""
    if request.user.is_authenticated:
        username = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f'You have been successfully logged out. Goodbye, {username}!')
    return redirect('login')
