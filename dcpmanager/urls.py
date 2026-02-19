from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views, api_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('session-management/', views.session_management, name='session_management'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.custom_logout, name='logout'),
    path('auth/', include('django.contrib.auth.urls')),
    path('api/session-status/', api_views.session_status, name='session_status'),
    path('employees/', include('employees.urls')),
    path('rbac/', include('rbac.urls')), # Include RBAC app URLs
    path('audit/', include('audit.urls')), # Include audit app URLs
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
